## Execute models

- Extract the downloaded .tar file of the cifar-100 dataset


- Give permissions to script
```
chmod u+x script_name.sh
```
- Execute script

```
./script_name.sh
```


## Models

### HD_CNN Baseline

The initial baseline of the HD-CNN Paper 

### ResNet Baseline

A simple vanilla ResNet-52

### Baseline Architecture

A modified ResNet-52 that in its middle a coarse prediction head is added and at the end a fine prediction head.

### ResNet Attention

Same modified ResNet as "Baseline Architecture" but with an attention layer added in between as described below. 


## Algorithm

### 1. Define the Coarse Classifier (CC) and the Fine Classifier (FC) for ResNet-50

#### CC consists of:
- ResNet Block: First two ConvBlocks of ResNet-50 (Input layer - "conv2_block3_out")
    - Input: Image (32x32x3)
    - Output: RO1 feature matrix
- Attention Block: Create heatmap of the images 
    - Input: Output RO1 (8x8x256)
    - Output: Input  RI1 (8x8x256)
- Prediction Layer:
    - Input: Output RO1 (8x8x256)
    - Output: 20 softmax units (Coarse labels)

#### FC consists of:
- ResNet Block: Third to Fifth ConvBlocks of ResNet-50 ("conv3_block1_1_conv" - "conv5_block3_out")
    - Input: RI1 + 20 coarse prediction labels
    - Output: RO2 feature matrix
- Prediction Bloack:
    - Input: RO2
    - Output: 100 softmax units (Fine labels)

### 2. Train CC

### 3. Freeze CC, Train FC

### 4. Fine-tune CC + FC together
