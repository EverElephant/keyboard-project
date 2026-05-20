#!/usr/bin/env python3
"""
xboard73 — KiCad PCB 自动生成脚本
73键客制化键盘 (nRF52840, 2×AA, BLE 无线)

用法: python3 gen_pcb.py
输出: ../xboard73.kicad_pcb
"""

import pcbnew
import os

# ============================================================
# 常量
# ============================================================
MM = 1_000_000  # 1mm = 1,000,000 nm (KiCad 内部用 nm)
U = round(19.05 * MM)  # 1u = 19.05mm (标准键间距)

# 库路径
FP_LIB = "/usr/share/kicad/footprints"

# 层 ID (KiCad 6)
LAYER_F_CU = 0
LAYER_IN1_CU = 1
LAYER_IN2_CU = 2
LAYER_B_CU = 3
LAYER_F_SILK = 31
LAYER_B_SILK = 32
LAYER_F_MASK = 33
LAYER_B_MASK = 34
LAYER_EDGE = 35

# 网络
NET_GND = 0
NET_VDD = 1

# 文件夹
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = SCRIPT_DIR


# ============================================================
# 工具函数
# ============================================================
def mm(val):
    """mm 转 nm"""
    return round(val * MM)


def u(val):
    """键单位转 nm"""
    return round(val * U)


def load_fp(name):
    """从 KiCad 库加载 Footprint"""
    for root, dirs, files in os.walk(FP_LIB):
        for f in files:
            if f == f"{name}.kicad_mod":
                path = os.path.join(root, f)
                fp = pcbnew.FootprintLoad(os.path.dirname(path), name)
                if fp:
                    return fp
    raise FileNotFoundError(f"Footprint {name} not found")


def place_fp(board, name, x_nm, y_nm, rot=0):
    """加载并放置一个 Footprint"""
    fp = pcbnew.FootprintLoad(
        os.path.dirname(os.path.join(FP_LIB, "dummy")), name
    )
    # Actually let me search the filesystem
    found = False
    for root, dirs, files in os.walk(FP_LIB):
        for f in files:
            if f == f"{name}.kicad_mod":
                fp = pcbnew.FootprintLoad(os.path.dirname(root), name)
                if fp:
                    found = True
                    break
        if found:
            break
    if not found or not fp:
        # Try loading by full path
        for root, dirs, files in os.walk(FP_LIB):
            for f in files:
                if f == f"{name}.kicad_mod":
                    full_path = os.path.join(root, f)
                    lib_dir = os.path.dirname(full_path)
                    fp_name = name
                    # KiCad footprint load needs the lib path and the name
                    try:
                        fp = pcbnew.FootprintLoad(lib_dir, fp_name)
                        if fp:
                            found = True
                        break
                    except:
                        continue
        if not found:
            # Last try - search by pattern
            for root, dirs, files in os.walk(FP_LIB):
                for f in files:
                    if name.lower() in f.lower() and f.endswith('.kicad_mod'):
                        name_exact = f.replace('.kicad_mod', '')
                        try:
                            fp = pcbnew.FootprintLoad(os.path.dirname(os.path.join(root, f)), name_exact)
                            if fp:
                                found = True
                            break
                        except:
                            continue
                if found:
                    break
        if not found:
            raise FileNotFoundError(f"Cannot find footprint: {name}")

    fp.SetPosition(pcbnew.wxPoint(int(x_nm), int(y_nm)))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)
    return fp


def add_track(board, x1, y1, x2, y2, layer=LAYER_F_CU, width=mm(0.15), net=0):
    """添加一条走线"""
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.wxPoint(int(x1), int(y1)))
    t.SetEnd(pcbnew.wxPoint(int(x2), int(y2)))
    t.SetLayer(layer)
    t.SetWidth(int(width))
    t.SetNetCode(net)
    board.Add(t)
    return t


def add_via(board, x, y, drill=mm(0.3), dia=mm(0.6)):
    """添加过孔"""
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.wxPoint(int(x), int(y)))
    v.SetDrill(int(drill))
    v.SetWidth(int(dia))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(v)
    return v


# ============================================================
# 配列位置定义 (相对于键盘左上角, 单位 mm)
# ============================================================

def xy(col, row):
    """
    返回键开关中心坐标 (mm)
    标准键矩阵: 19.05mm 间距, 行偏移 0.25u 交错
    col: 列号 (0=左侧列, 1-15=主体区)
    row: 行号 (0-5)
    """
    x_base = 9.525  # 左侧列中心 x = 0.5u
    main_start_x = 38.1  # 主体区起始 x = 2u (半格间距)

    if col == 0:
        x = x_base + 0
    else:
        x = main_start_x + (col - 1) * 19.05

    row_stagger = [0, 4.7625, 9.525, 14.2875, 14.2875, 0]
    y = row * 19.05 + row_stagger[row]
    return x, y


# ============================================================
# 主函数
# ============================================================
def main():
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()

    # --- 设计规则 ---
    ds.m_TrackMinWidth = int(mm(0.15))
    ds.m_ViasMinSize = int(mm(0.4))
    ds.m_ViasMinDrill = int(mm(0.2))
    # Clearance
    ds.m_TrackMinClearance = int(mm(0.15))
    ds.m_ZoneMinClearance = int(mm(0.3))

    # --- 层叠: 4 层板 ---
    board.SetCopperLayerCount(4)
    board.SetLayerName(LAYER_IN1_CU, "GND")
    board.SetLayerName(LAYER_IN2_CU, "VDD")

    # --- 按键布局 (73 键) ---
    # 配列定义: (col, row, 键名)
    keys = []

    # 左侧列 (col=0)
    left_col_keys = ["Esc", "F1", "F2", "F3", "F4"]
    for r, name in enumerate(left_col_keys):
        keys.append((0, r, name))

    # Row 0: ` 1 2 3 4 5 6 7 8 9 0 - = Bksp
    row0 = ["Grv", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Bsp"]
    for c, name in enumerate(row0):
        keys.append((1 + c, 0, name))

    # Row 1: Tab Q W E R T Y U I O P [ ] \
    row1 = ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"]
    for c, name in enumerate(row1):
        keys.append((1 + c, 1, name))

    # Row 2: Caps A S D F G H J K L ; ' Enter(2u)
    row2_names = ["Cap", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'"]
    for c, name in enumerate(row2_names):
        keys.append((1 + c, 2, name))
    # Enter (2u) at position 14
    keys.append((14, 2, "Ent"))

    # Row 3: Shift Z X C V B N M , . / Shift(2u)
    row3_names = ["Sft", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
    for c, name in enumerate(row3_names):
        keys.append((1 + c, 3, name))
    # RShift at position 13
    keys.append((13, 3, "RSft"))

    # Row 4: Ctrl Win Alt Space(6.25u) Alt Fn Ctrl
    row4_names = ["LCt", "Win", "Alt", "Spc", "Alt", "Fn", "RCt"]
    for c, name in enumerate(row4_names):
        keys.append((1 + c, 4, name))

    # Row 5: Ins Del PgUp PgDn ↑ ← ↓ →
    row5_names = ["Ins", "Del", "PU", "PD", "Up", "Lf", "Dn", "Rt"]
    for c, name in enumerate(row5_names):
        keys.append((1 + c, 5, name))

    # --- 放置键开关 ---
    for col, row, kname in keys:
        x_pos, y_pos = xy(col, row)
        try:
            fp = place_fp(board, "SW_Cherry_MX_1.00u_Plate",
                         mm(x_pos), mm(y_pos))
            fp.SetReference(f"SW_{kname}")
            fp.SetValue(kname)
        except FileNotFoundError as e:
            print(f"  [WARN] {e}")
            continue

    # --- 放置 nRF52840 ---
    mcu_x = mm(200)
    mcu_y = mm(80)
    try:
        fp = place_fp(board,
            "Nordic_AQFN-73-1EP_7x7mm_P0.5mm",
            mcu_x, mcu_y)
        fp.SetReference("U1")
        fp.SetValue("nRF52840")
    except FileNotFoundError as e:
        print(f"  [WARN] {e}")

    # --- 放置晶振 ---
    try:
        fp = place_fp(board,
            "Crystal_SMD_3225-4Pin_3.2x2.5mm_HandSoldering",
            mcu_x + mm(12), mcu_y - mm(15))
        fp.SetReference("X1")
        fp.SetValue("32MHz")
    except FileNotFoundError as e:
        print(f"  [WARN] {e}")

    try:
        fp = place_fp(board,
            "Crystal_SMD_3215-2Pin_3.2x1.5mm",
            mcu_x + mm(12), mcu_y + mm(15))
        fp.SetReference("X2")
        fp.SetValue("32.768kHz")
    except FileNotFoundError as e:
        print(f"  [WARN] {e}")

    # --- 去耦电容 (0603) ---
    cap_positions = [
        (mcu_x + mm(-5), mcu_y + mm(-8)),
        (mcu_x + mm(-5), mcu_y + mm(8)),
        (mcu_x + mm(-10), mcu_y + mm(-8)),
        (mcu_x + mm(-10), mcu_y + mm(8)),
    ]
    for i, (cx, cy) in enumerate(cap_positions):
        try:
            fp = place_fp(board, "C_0603_1608Metric", cx, cy)
            fp.SetReference(f"C{i+1}")
            fp.SetValue("0.1uF" if i < 2 else "4.7uF")
        except FileNotFoundError:
            pass

    # --- 放置二极管 (73x SOD-123) ---
    # 放置在每个键旁边
    for idx, (col, row, kname) in enumerate(keys):
        x_pos, y_pos = xy(col, row)
        # Diode slightly above each switch
        dx = mm(x_pos)
        dy = mm(y_pos - 10)  # 10mm above switch center
        try:
            fp = place_fp(board, "D_SOD-123", dx, dy)
            fp.SetReference(f"D{idx+1}")
        except FileNotFoundError:
            pass

    # --- 板框 (Edge Cuts) ---
    # 计算板子尺寸
    max_x = 0
    max_y = 0
    for col, row, kname in keys:
        x, y = xy(col, row)
        max_x = max(max_x, x + 12)  # 半键余量
        max_y = max(max_y, y + 12)

    board_w = mm(max_x + 10)  # mm to nm
    board_h = mm(max_y + 10)

    dc = pcbnew.PCB_SHAPE(board)
    dc.SetShape(pcbnew.SHAPE_T_RECT)
    dc.SetStart(pcbnew.wxPoint(0, 0))
    dc.SetEnd(pcbnew.wxPoint(int(board_w), int(board_h)))
    dc.SetLayer(LAYER_EDGE)
    dc.SetWidth(mm(0.1))
    board.Add(dc)

    # --- 保存 ---
    out_path = os.path.join(OUT_DIR, "xboard73.kicad_pcb")
    pcbnew.SaveBoard(out_path, board)
    print(f"\n✅ PCB 已保存: {out_path}")
    print(f"   板尺寸: {board_w/MM:.1f} x {board_h/MM:.1f} mm")
    print(f"   按键数: {len(keys)}")
    print(f"   层数: 4")


if __name__ == "__main__":
    main()
