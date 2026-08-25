# PEOD: A Pixel-Aligned Event-RGB Benchmark for Object Detection under Challenging Conditions

<div align="center"

<div align="center">

[![Project Page](https://img.shields.io/badge/🌐_Project_Page-Visit_Our_Website-blue?style=for-the-badge)](https://EchosLiu.github.io/PEOD-dataset/)
[![Paper](https://img.shields.io/badge/📄_Paper-AAAI_2026-red?style=for-the-badge)](https://arxiv.org/abs/2511.08140)
[![Dataset](https://img.shields.io/badge/📊_Dataset-Download-green?style=for-the-badge)](https://drive.google.com/drive/folders/19W2EJUXXtVZA24_PuAQN_n275QjpuV89?usp=sharing)

[**🚀 Visualization**](https://EchosLiu.github.io/PEOD-dataset/) | [**📥 Baidu Link**](https://pan.baidu.com/s/1Mj4tpGBFzSyhz6dZX0dDrw?pwd=g97d) | [**📥 Google Link**](https://drive.google.com/drive/folders/19W2EJUXXtVZA24_PuAQN_n275QjpuV89?usp=sharing)

</div>

---

## 🎯 Overview

**PEOD** is the first large-scale dataset providing synchronized high-resolution event streams and RGB images for object detection under challenging conditions. This groundbreaking dataset addresses the critical need for robust perception systems that can operate reliably across diverse environmental conditions, particularly in scenarios where traditional frame-based sensors struggle.

<div align="center">
<img src="assets/images/datasetshow.png" alt="PEOD Dataset Overview" width="800"/>
</div>

### 🔬 Key Contributions

- **🎥 High-Resolution Multimodal Data**: 1280×720 pixel-aligned event streams and RGB frames captured using a coaxial dual-camera system
- **🌍 Comprehensive Coverage**: 120+ driving sequences across urban, suburban, and tunnel environments
- **🌙 Challenging Conditions**: 57% of data collected under low light, overexposed, or high-speed conditions
- **🏷️ Rich Annotations**: 340k manually verified bounding boxes across six object classes
- **⚡ High Dynamic Range**: Event camera with >87 dB HDR for extreme illumination scenarios

## 📊 Dataset Statistics

| **Metric** | **Value** | **Description** |
|------------|-----------|-----------------|
| **Resolution** | 1280×720 | High-resolution pixel-aligned streams |
| **Sequences** | 120+ | Diverse driving scenarios |
| **Total Frames** | 72k | Synchronized RGB and event data |
| **Annotations** | 340k | Manually verified bounding boxes |
| **Frequency** | 30 Hz | High-frequency data capture |
| **Classes** | 6 | car, bus, truck, two-wheeler, three-wheeler, person |
| **Dynamic Range** | >87 dB | Event camera HDR capability |

## 📁 Dataset Structure

```
PEOD/
├── rgb/
│   ├── train/
│   │   ├── sequence_001                       # the first RGB sequence
│   │   │   ├── sequence_001_0001.png          # the first RGB frame
│   │   │   ├── sequence_001_0001.png          # the second RGB frame
│   │   │   └── ...
│   │   ├── sequence_002                       # the second RGB sequence
│   │   └── ...                                
│   └── test/
│   │   ├── challenge/                         # the Illumination Challenge Subset
│   │   │   ├── sequence_001_test              # the first illumination challenge sequence
│   │   │   └── ...
│   │   └── nromal/                            # the Normal Subset
│   │   │   ├── sequence_013_test              # the first normal sequence
│   │   │   └── ...
├── event/
│   ├── train/
│   │   ├── sequence_001.dat              
│   │   ├── sequence_002.dat
│   │   └── ...              
│   └── test/
│   │   ├── challenge/                         
│   │   │   ├── sequence_001_test.dat          
│   │   │   └── ...
│   │   └── nromal/                            
│   │   │   ├── sequence_013_test.dat            
│   │   │   └── ...
├── timestamp/
│   └── [similar structure]
└── annotations/
    └── [similar structure]
```

## 🎯 Object Classes

The dataset includes six carefully selected object classes relevant to autonomous driving:

| **Class** | **Description** | **Typical Scenarios** |
|-----------|-----------------|----------------------|
| **Car** | Standard passenger vehicles | Urban/suburban driving |
| **Person** | Pedestrians | Crosswalks, sidewalks |
| **Bus** | Public transportation vehicles | City centers, bus routes |
| **Truck** | Commercial vehicles | Highways, industrial areas |
| **Two-wheeler** | Motorcycles, bicycles | Urban intersections |
| **Three-wheeler** | Auto-rickshaws, tricycles | Developing urban areas |


## 🌟 Unique Features

### 🔄 Perfect Pixel Alignment
Our coaxial dual-camera system ensures precise spatial correspondence between event and RGB data, enabling accurate multimodal fusion.

### 🌓 Challenging Conditions
- **Low light scenarios**: Twilight, dawn, underground passages
- **High-speed motion**: Highway driving, rapid camera movements  
- **Extreme illumination**: Direct sunlight, headlight glare, tunnel exits

### ⚡ Event Camera Advantages
- **High temporal resolution**: Microsecond precision
- **High dynamic range**: >87 dB vs ~60 dB for standard cameras
- **Motion blur immunity**: Sharp perception during rapid movement
- **Low latency**: Real-time perception capabilities

## 📥 Download

> **Dataset Download**: The PEOD dataset can be downloaded from [Baidu Netdisk](https://pan.baidu.com/s/1Mj4tpGBFzSyhz6dZX0dDrw?pwd=g97d) or [Google Drive](https://drive.google.com/drive/folders/19W2EJUXXtVZA24_PuAQN_n275QjpuV89?usp=sharing).


## 🧩 Benchmark Methods

The following methods are included in the PEOD benchmark:

- **[ICCV 2017] RetinaNet**: *Focal Loss for Dense Object Detection* [[Paper](https://arxiv.org/abs/1708.02002)] [[Code](https://github.com/bubbliiiing/retinanet-pytorch)]
- **[arXiv 2021] YOLOX**: *YOLOX: Exceeding YOLO Series in 2021* [[Paper](https://arxiv.org/abs/2107.08430)] [[Code](https://github.com/Megvii-BaseDetection/YOLOX)]
- **[ICRA 2022] FPN-Fusion**: *Fusing Event-based and RGB Camera for Robust Object Detection in Adverse Conditions* [[Paper](https://hal.science/hal-03591717)] [[Code](https://github.com/abhishek1411/event-rgb-fusion)]
- **[ICRA 2023] RENet**: *RGB-Event Fusion for Moving Object Detection in Autonomous Driving* [[Paper](https://arxiv.org/abs/2209.08323)] [[Code](https://github.com/ZZY-Zhou/RENet)]
- **[TPAMI 2023] SODFormer**: *Streaming Object Detection with Transformer Using Events and Frames* [[Paper](https://arxiv.org/abs/2308.04047)] [[Code](https://github.com/dianzl/SODFormer)]
- **[CVPR 2023] RVT**: *Recurrent Vision Transformers for Object Detection with Event Cameras* [[Paper](https://arxiv.org/abs/2212.05598)] [[Code](https://github.com/uzh-rpg/RVT)]
- **[CVPR 2023] YOLOv7**: *YOLOv7: Trainable Bag-of-Freebies Sets New State-of-the-Art for Real-Time Object Detectors* [[Paper](https://arxiv.org/abs/2207.02696)] [[Code](https://github.com/WongKinYiu/yolov7)]
- **[CVPR 2024] SAST**: *Scene Adaptive Sparse Transformer for Event-based Object Detection* [[Paper](https://arxiv.org/abs/2404.01882)] [[Code](https://github.com/Peterande/SAST)]
- **[ECCV 2024] SpikingYOLO**: *Integer-Valued Training and Spike-Driven Inference Spiking Neural Network for High-performance and Energy-efficient Object Detection* [[Paper](https://arxiv.org/abs/2407.20708)] [[Code](https://github.com/BICLab/SpikeYOLO)]
- **[CVPR 2024] RT-DETR**: *DETRs Beat YOLOs on Real-time Object Detection* [[Paper](https://arxiv.org/abs/2304.08069)] [[Code](https://github.com/lyuwenyu/RT-DETR)]
- **[ICRA 2024] EOLO**: *Chasing Day and Night: Towards Robust and Efficient All-Day Object Detection Guided by an Event Camera* [[Paper](https://arxiv.org/abs/2309.09297)] [[Code](https://github.com/SageCao1125/EOLO)]
- **[T-ITS 2024] SFNet**: *Enhancing Traffic Object Detection in Variable Illumination with RGB-Event Fusion* [[Paper](https://arxiv.org/abs/2311.00436)] [[Code](https://github.com/Zizzzzzzz/SFNet_T-ITS24)]
- **[ECCV 2024] CAFR**: *Embracing Events and Frames with Hierarchical Feature Refinement Network for Object Detection* [[Paper](https://arxiv.org/abs/2407.12582)] [[Code](https://github.com/HuCaoFighting/FRN)]
- **[AAAI 2025] SMamba**: *SMamba: Sparse Mamba for Event-based Object Detection* [[Paper](https://arxiv.org/abs/2501.11971)] [[Code](https://github.com/Zizzzzzzz/SMamba_AAAI2025)]


## 📚 Citation

If you use PEOD in your research, please cite our paper:

```bibtex
@article{cui2025peod,
  title={PEOD: A Pixel-Aligned Event-RGB Benchmark for Object Detection under Challenging Conditions},
  author={Cui, Luoping and Liu, Hanqing and Liu, Mingjie and Lin, Endian and Jiang, Donghong and Wang, Yuhao and Zhu, Chuang},
  journal={arXiv preprint arXiv:2511.08140},
  year={2025}
}
```

## 🤝 Contributing

We welcome contributions to improve the dataset and benchmark! Please see our [project page](https://EchosLiu.github.io/PEOD-dataset/) for contribution guidelines.

## 📄 License

This dataset is released under MIT License. Please refer to our [License](https://github.com/bupt-ai-cz/PEOD/blob/main/Term%20of%20Use%20and%20License.md) for detailed licensing information.

## Contact

For questions, suggestions, or collaboration opportunities:

- **Project Page**: [https://EchosLiu.github.io/PEOD-dataset/](https://EchosLiu.github.io/PEOD-dataset/)
- **Issues**: Please use GitHub Issues for technical questions
- **Email**: 3254827845@qq.com；3371665749@qq.com；echosliu@outlook.com；czhu@bupt.edu.cn

---

<div align="center">

**🌟 Star this repository if you find PEOD useful for your research! 🌟**

[![GitHub stars](https://img.shields.io/github/stars/bupt-ai-cz/PEOD?style=social)](https://github.com/bupt-ai-cz/PEOD/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/bupt-ai-cz/PEOD?style=social)](https://github.com/bupt-ai-cz/PEOD/network/members)

</div>
