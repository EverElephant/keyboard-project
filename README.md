# keyboard-project

客制化键盘项目 — 73 键配列（68 左加半格 5 键）

## 目录结构
- `pcb/` — PCB 设计文件（待画）
- `firmware/zmk-config/` — ZMK 固件配置
  - `config/xboard73.keymap` — 按键映射
  - `config/xboard73.conf` — 主控配置
  - `boards/shields/xboard73/` — 自定义 shield 定义
  - `build.yaml` — 构建配置
- `case/` — 外壳 3D 模型
- `docs/` — 文档
  - `docs/pcb-design.md` — PCB 设计说明（原理图、BOM、Layout 检查清单）

## 硬件方案
- 主控：nRF52840-QIAA-R
- 外壳：待定（CNC 塑料 / 亚克力堆叠）
- 配列：73 键（标准 68 + 左侧半格间距 5 列键 Esc/F1-F4）
- 电源：2×AA 串联（3.0V），PMOS 开关
- 无线：BLE 5.0（板载天线）

## 状态

| 模块 | 状态 |
|------|------|
| 固件骨架 | ✅ 已定义（overlay + keymap + config） |
| PCB 设计说明 | ✅ 完整原理图 + BOM + Layout 检查清单 |
| PCB 画板 | ⏳ EasyEDA 待画 |
| 外壳 | ⏳ 已有旧版 AutoCAD 模型，后续可重做 |
| 编译/烧录 | ⏳ CI 或本地工具链待配置 |
