import tensorflow as tf
import logging
import numpy as np
import utils
import json

logger = logging.getLogger('ResNetBaseline')


class ResNetAttention:
    def __init__(self, n_fine_categories, n_coarse_categories, input_shape,
                 logs_directory=None, model_directory=None, args=None):
        """
        ResNet baseline model

        """
        self.model_directory = model_directory
        self.args = args
        self.n_fine_categories = n_fine_categories
        self.n_coarse_categories = n_coarse_categories
        self.input_shape = input_shape

        logger.debug(f"Creating full classifier with shared layers")
        self.full_classifier = self.build_full_classifier()

        self.tbCallBack = tf.keras.callbacks.TensorBoard(
            log_dir=logs_directory, histogram_freq=0,
            write_graph=True, write_images=True)

        self.training_params = {
            'batch_size': 64,
            'initial_epoch': 0,
            'step': 5,  # Save weights every this amount of epochs
            'stop': 30
        }

        self.prediction_params = {
            'batch_size': 64
        }

    def train(self, training_data, validation_data):
        x_train, y_train = training_data
        x_val, y_val = validation_data

        p = self.training_params

        adam_coarse = tf.keras.optimizers.Adam(lr=0.001, decay=1e-6)
        self.full_classifier.compile(optimizer=adam_coarse,
                                     loss='categorical_crossentropy',
                                     metrics=['accuracy'])
        index = p['initial_epoch']
        while index < p['stop']:
            self.full_classifier.fit(x_train, y_train,
                                     batch_size=p['batch_size'],
                                     initial_epoch=index,
                                     epochs=index + p['step'],
                                     validation_data=(x_val, y_val),
                                     callbacks=[self.tbCallBack])
            index += p['step']

    def predict_fine(self, testing_data, results_file):
        x_test, y_test = testing_data

        p = self.prediction_params

        yh_s = self.full_classifier.predict(x_test, batch_size=p['batch_size'])

        single_classifier_error = utils.get_error(y_test, yh_s)
        logger.info('Single Classifier Error: '+str(single_classifier_error))

        results_dict = {'Single Classifier Error': single_classifier_error}
        self.write_results(results_file, results_dict=results_dict)

        return yh_s

    def predict_coarse(self, testing_data, results_file, fine2coarse):
        x_test, y_test = testing_data

        p = self.prediction_params

        yh_s = self.full_classifier.predict(x_test)

        single_classifier_error = utils.get_error(y_test, yh_s)
        logger.info('Single Classifier Error: ' + str(single_classifier_error))

        yh_c = np.dot(yh_s, fine2coarse)
        y_test_c = np.dot(y_test, fine2coarse)
        coarse_classifier_error = utils.get_error(y_test_c, yh_c)

        logger.info('Single Classifier Error: ' + str(coarse_classifier_error))
        results_dict = {'Single Classifier Error': single_classifier_error,
                        'Coarse Classifier Error': coarse_classifier_error}
        self.write_results(results_file, results_dict=results_dict)

    def write_results(self, results_file, results_dict):
        for a, b in results_dict.items():
            # Ensure that results_dict is made by numbers and lists only
            if type(b) is np.ndarray:
                results_dict[a] = b.tolist()
        json.dump(results_dict, open(results_file, 'w'))

    def build_full_classifier(self):

        # Define ResNet
        base_model = tf.keras.applications.resnet.ResNet50(include_top=False, weights='imagenet',
                                                           input_tensor=None, input_shape=self.input_shape,
                                                           pooling=None, classes=1000)

        # Define CC ResNet Block
        model_cc_resnet = tf.keras.Model(inputs=base_model.input, outputs=base_model.get_layer('conv2_block3_out').output)

        # Define CC Attention Block
        weights = tf.reduce_sum(model_cc_resnet.output, axis=(1, 2))
        weights = tf.math.l2_normalize(weights, axis=1)
        weights = tf.expand_dims(weights, axis=1)
        weights = tf.expand_dims(weights, axis=1)
        weigthed_channels = tf.multiply(model_cc_resnet.output, weights)
        attention_map = tf.reduce_sum(weigthed_channels, 3)

        # Define CC Prediction Block
        cc_flat = tf.keras.layers.Flatten()(model_cc_resnet.output)
        cc_out = tf.keras.layers.Dense(
           self.n_coarse_categories, activation='softmax')(cc_flat)

        # Build CC
        cc_model = tf.keras.models.Model(inputs=model_cc_resnet.input, outputs=cc_out)

        # Define FC input
        fc_in = tf.keras.layers.concatenate([attention_map, cc_out])

        # Define FC ResNet Block
        model_fc_resnet = tf.keras.Model(inputs=base_model.get_layer('conv3_block1_1_conv'),
                                         outputs=base_model.get_layer('conv5_block3_out').output)

        # Define FC output
        fc_flat = tf.keras.layers.Flatten()(model_fc_resnet.output)
        fc_out = tf.keras.layers.Dense(
           self.n_fine_categories, activation='softmax')(fc_flat)

        # Build FC
        fc_model = tf.keras.models.Model(inputs=fc_in, outputs=fc_out)

        return cc_model, fc_model
