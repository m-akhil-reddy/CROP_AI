# Dataset Directory

Place your crop damage image dataset here, organized by class subfolders.

## Required Structure

```
dataset/
├── Animal_Damage/
│   ├── img001.jpg
│   ├── img002.jpg
│   └── ...
├── Disease/
│   ├── img001.jpg
│   └── ...
├── Drought/
├── Flood/
├── Healthy/
├── Heavy_Rain/
├── Insect_Attack/
└── Nutrient_Deficiency/
```

## Important Notes

- Each subfolder name **must exactly match** a label in `config.py → DAMAGE_CLASSES`
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`
- Recommended: **500+ images per class** for good accuracy
- Minimum: **50 images per class** to start training

## Recommended Datasets

1. **PlantVillage Dataset** (Kaggle)
   - URL: https://www.kaggle.com/datasets/emmarex/plantdisease
   - Contains: 54,000+ images of healthy and diseased plant leaves

2. **Rice Disease Dataset** (Kaggle)
   - URL: https://www.kaggle.com/datasets/tedisetiady/leaf-rice-disease-detection

3. **Crop Damage Dataset**
   - URL: https://www.kaggle.com/datasets/smaranjitghose/corn-or-maize-leaf-disease-dataset

## How to Train

After placing images in the correct subfolders:

```bash
cd backend
python -m ml.train
```

The trained model will be saved to `saved_models/crop_damage_model.h5`
and the server will automatically switch to real CNN inference on the next restart.
