# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['PyZebraScope.py'],
             pathex=['C:\\Users\\LS_User\\Desktop\\PyZebraScope'],
             binaries=[],
             datas=[('C:\\Users\\LS_User\\Desktop\\PyZebraScope\\zebrafish_whole_small.png', '.')],
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
          name='PyZebraScope',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='PyZebrascope.ico')
