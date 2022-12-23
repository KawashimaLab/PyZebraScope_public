
block_cipher = None

a = Analysis(['PyZebraScope.py'],
             pathex=['C:\\Users\\LS_User\\Desktop\\PyZebraScope'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

a.datas += Tree('C:\\Users\\LS_User\\anaconda3\\Lib\\site-packages\\cupy\\_core', 'C:\\Users\\LS_User\\anaconda3\\Lib\\site-packages\\cupy\\_core', 
	excludes=['_accelerator.cp37-win_amd64.pyd',
        '_dtype.cp37-win_amd64.pyd',
        '_fusion_thread_local.cp37-win_amd64.pyd',
        '_kernel.cp37-win_amd64.pyd',
        '_memory_range.cp37-win_amd64.pyd',
        '_optimize_config.cp37-win_amd64.pyd',
        '_reduction.cp37-win_amd64.pyd',
        '_routines_binary.cp37-win_amd64.pyd',
        '_routines_indexing.cp37-win_amd64.pyd',
        '_routines_linalg.cp37-win_amd64.pyd',
        '_routines_logic.cp37-win_amd64.pyd',
        '_routines_manipulation.cp37-win_amd64.pyd',
        '_routines_math.cp37-win_amd64.pyd',
        '_routines_statistics.cp37-win_amd64.pyd',
        '_scalar.cp37-win_amd64.pyd',
        'core.cp37-win_amd64.pyd',
        'dlpack.cp37-win_amd64.pyd',
        'fusion.cp37-win_amd64.pyd',
        'internal.cp37-win_amd64.pyd',
        'raw.cp37-win_amd64.pyd'])

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
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='PyZebrascope.ico')

hiddenimports = ['cupy_backends.cuda.stream','fastrlock', 'fastrlock.rlock' ]
