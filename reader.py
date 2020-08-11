import io
import sys
import re

import pandas as pd

FILE = None
SUBCASE = 4
HEADER = "F O R C E S   I N   B A R   E L E M E N T S"
ROW_OFFSET = 3

COLUMNS = [
    "ELEMENT",
    "DISTANCE",
    "BENDING_MOMENT_PLANE_1",
    "BENDING_MOMENT_PLANE_2",
    "SHEAR_FORCE_PLANE_1",
    "SHEAR_FORCE_PLANE_2",
    "AXIAL_FORCE",
    "TORQUE",
]

if len(sys.argv) < 2:
    raise "No filename provided"
else:
    with open(sys.argv[1]) as f:
        FILE = f.read()


def find_subcase_regex(subcase, header):
    return re.compile(
        rf"SUBCASE\s{SUBCASE}\s*{HEADER}\n([\s\S]*?)(?:\d{{2}}\/){{2}}\d{{2}}"
    )


def find_frames(subcase, header, file=FILE):
    """
    This is just a utility method to clean up the dataframes into
    something usable.  The masking and shifting is required because
    the first column is sparse since it's probably an index in MATLAB.

    If you can make that code spit out dense data it makes ingestion a
    lot easier here.
    """
    for match in re.finditer(find_subcase_regex(subcase, header), file):
        lines = "\n".join(match.group(1).split("\n")[ROW_OFFSET:])
        strio = io.StringIO(lines)
        df = pd.read_csv(strio, sep=r"\s+", header=None)
        masked = df.iloc[:, -1].isna()
        df[masked] = df[masked].shift(1, axis=1)
        df.iloc[:, 0] = df.iloc[:, 0].ffill().astype(int)
        df.columns = COLUMNS
        df["NODE"] = df.groupby(COLUMNS[0]).cumcount().map({0: "A", 1: "B"})
        yield df.set_index([COLUMNS[0], "NODE"])


df = pd.concat(list(find_frames(4, HEADER)))

# Now that we have cleaned data, we can use vectorized operations
# on a DataFrame
ELEMENTS = [1097, 1076, 1041, 1037, 1145, 1187]
NODES = ["A", "A", "B", "B", "B", "A"]

df_a = df.loc[zip(ELEMENTS, NODES)]

NEW_ORDER = [
    "AXIAL_FORCE",
    "SHEAR_FORCE_PLANE_1",
    "SHEAR_FORCE_PLANE_2",
    "TORQUE",
    "BENDING_MOMENT_PLANE_2",
    "BENDING_MOMENT_PLANE_1",
]

df_a = df_a[NEW_ORDER]
df_a.columns = ["Fx", "Fy", "Fz", "Mx", "My", "Mz"]

print(df_a)
