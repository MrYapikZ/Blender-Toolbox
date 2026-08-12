# DelthλTools

**Blender addon** berisi kumpulan tool produksi untuk Asset, Animator, dan Lighting/Compositing/Render.

- **Versi:** 0.3.0
- **Blender:** 5.2.0
- **Author:** Yapi

---

## Fitur

### Asset Tool
| Tool | Deskripsi |
|---|---|
| [Asset Collection Rename](docs/features/asset-collection-rename.md) | Rename otomatis seluruh objek dalam collection sesuai nama project |
| [Fix Image Windows Path](docs/features/fix-image-windows-path.md) | Deteksi & perbaiki missing image path dari format Windows ke Linux |

### Animator Tool
| Tool | Deskripsi |
|---|---|
| [Animation Playblast Render](docs/features/animation-playblast-render.md) | Render preview animasi dengan preset & output path otomatis dari ExConfig |
| [Quick Open Graph Window](docs/features/quick-open-graph-window.md) | Buka Graph Editor di jendela baru dengan satu klik |

### Lighting, Compositing & Render Tool
| Tool | Deskripsi |
|---|---|
| [Character Three Point Light Setup](docs/features/character-three-point-light-setup.md) | Append 3-point lighting untuk karakter, otomatis Child Of & Light Linking |
| [Character Three Point Light Properties](docs/features/character-three-point-light-properties.md) | Export/Import preset JSON lighting, Make Override Local, Override Fog |
| [Eye Glow Compositing](docs/features/eye-glow-compositing.md) | Setup node Cryptomatte + Eye_Glow_Setup di Compositor secara otomatis |

---

## Instalasi

1. Download atau clone repository ini
2. Di Blender, buka **Edit → Preferences → Add-ons → Install**
3. Pilih folder root project ini (atau file `.zip` jika sudah dikemas)
4. Aktifkan addon **DelthλTools**
5. Buka **3D Viewport → Sidebar (N) → DelthλTools**

---

## Struktur Project

```
DelthaTools/
├── __init__.py          # Entry point addon, bl_info
├── ops/                 # Operator (logika tool)
│   ├── AnimPlayblast/
│   ├── AssetColRename/
│   ├── ExConfig/
│   ├── ExLauncher/
│   ├── EyeGlowCompositing/
│   ├── GraphNewWindow/
│   ├── ImgWinPath/
│   ├── LightingProperties/
│   └── LightingSetup/
├── ui/                  # Panel UI Blender
├── pref/                # PropertyGroup (data scene)
├── utils/               # Utility (file manager, config, dll.)
├── presets/             # File preset (blend, JSON)
└── docs/                # Dokumentasi
    ├── features/        # Dokumentasi per fitur
    └── images/          # Screenshot panduan
```

---

## Dokumentasi

Dokumentasi lengkap tersedia di folder [`docs/`](docs/SUMARRY.md).
