import sys
sys.setrecursionlimit(5000)
block_cipher = None
from glob import glob
import os


datas = [('taplt/icons', 'taplt/icons')]
datas += [('taplt/macros/examples/images', 'taplt/macros/examples/images')]

a = Analysis(['taplt/__main__.py'],
             binaries=[],
             datas=datas,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='taplt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False)