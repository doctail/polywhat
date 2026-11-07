"""Install MPFB 2 (MakeHuman plugin for Blender, GPL code / CC0 assets) as a user extension.
   blender -b -P tools/city/install_mpfb.py -- /path/to/mpfb2_checkout
The checkout comes from  git clone --depth 1 https://github.com/makehumancommunity/mpfb2"""
import sys, os, shutil, tempfile, addon_utils
import bpy
src = sys.argv[sys.argv.index('--') + 1]
tmp = tempfile.mkdtemp(); z = shutil.make_archive(os.path.join(tmp, 'mpfb'), 'zip', os.path.join(src, 'src'), 'mpfb')
bpy.ops.extensions.package_install_files(filepath=z, repo='user_default', enable_on_install=True)
bpy.ops.wm.save_userpref()
print('[mpfb] installed:', 'bl_ext.user_default.mpfb' in sys.modules)
