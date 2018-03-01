"""
Create an MSI package using the WIX toolset

We adopt the rule of 'one file per component' as suggested although this requires thousands
of components. Generation of GUIDs is accomplished by using the Python UUID library to generate 
the ID based on a hash of the file path. This should ensure that the GUIDs are specific to the
file path (as required) and also reproducible (as required). 

The same technique is used to generate the product, upgrade GUID, using fixed notional paths
for reproducibility
"""
import os, sys
import uuid
import shutil
from StringIO import StringIO

MSI_SUBDIR = "msi"

# Path to WIX toolset - update as required
WIXDIR = "c:\Program Files (x86)/WiX Toolset v3.11/bin/"

# Main template for our WXS file - content is added using the Python
# string formatting placeholders
WXS_TEMPLATE = """
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
   <!-- MSI configuration for %(name)s -->

   <!-- Basic product information -->
   <Product Id="*" 
            UpgradeCode="%(upgrade_guid)s" 
            Name="%(name)s" 
            Version="%(version_str)s" 
            Manufacturer="ibme-qubic" 
            Language="1033">
      <Package Id="*" 
               InstallerVersion="200" 
               Compressed="yes" 
               Comments="Windows Installer Package"
               Platform="x64"/>
      <Media Id="1" 
             Cabinet="product.cab" 
             EmbedCab="yes"/>
      <MajorUpgrade AllowDowngrades="no" 
                    DowngradeErrorMessage="Cannot downgrade to lower version - remove old version first"
                    AllowSameVersionUpgrades="no"/>


      <Directory Id="TARGETDIR" Name="SourceDir">
        <!-- Program files -->
        <Directory Id="ProgramFiles64Folder">
          <Directory Id="QuantiphyseFolder" Name="quantiphyse">
            <Directory Id="PackagesFolder" Name="packages">
              <Directory Id="PluginsFolder" Name="plugins">
%(dist_files)s 
              </Directory>
            </Directory>
          </Directory>
        </Directory>
      </Directory>

      <!-- No custom features - all or nothing -->
      <Feature Id="Complete" Level="1">
%(features)s
      </Feature>

      <!-- User interface configuration -->
      <Property Id="WIXUI_INSTALLDIR" Value="INSTALLDIR" />
      <UIRef Id="WixUI_Minimal" />
      <UIRef Id="WixUI_ErrorProgressText" />
      <WixVariable Id="WixUIBannerBmp" Value="packaging/images/banner.bmp" />
      <WixVariable Id="WixUIDialogBmp" Value="packaging/images/dialog.bmp" />
      <!--WixVariable Id="WixUILicenseRtf" Value="packaging/LICENSE.rtf"/-->

      <!--Icon Id="main_icon.ico" SourceFile="quantiphyse/icons/main_icon.ico" />
      <Property Id="ARPPRODUCTICON" Value="main_icon.ico" /-->
   </Product>
</Wix>"""

# Minimal RTF template used to turn the license text into RTF
RTF_TEMPLATE = """{\\rtf
{\\fonttbl {\\f0 Courier;}}
\\f0\\fs20 %s
}"""

def get_guid(path):
    """
    Return a GUID which is reproducibly tied to a file path
    """
    return uuid.uuid5(uuid.NAMESPACE_DNS, 'quantiphyse.org/' + os.path.normpath(path))

def add_files_in_dir(distdir, pkgdir, nfile, ndir, output, indent):
    """
    Add file componenents from a directory, recursively adding from subdirs
    """
    output.write('%s<Directory Id="INSTALLDIR%i" Name="%s">\n' % (indent, ndir, os.path.basename(pkgdir)))
    ndir += 1
    for dirName, subdirList, fileList in os.walk(os.path.join(distdir, pkgdir)):
        for fname in fileList:
            srcpath = os.path.join(distdir, pkgdir, fname)
            
            # Generate GUID based on destination path relative to install location
            destpath = os.path.join("quantiphyse", "packages", "plugins", pkgdir, fname)
            guid = get_guid(destpath)

            # Write component XML
            output.write('%s  <Component Id="Component%i" Guid="%s" Win64="yes">\n' % (indent, nfile, str(guid)))
            output.write('%s    <File Id="File%i" Source="%s" KeyPath="yes"/>\n' % (indent, nfile, srcpath))
            output.write('%s  </Component>\n' % indent)
            nfile += 1
        for child in subdirList:
            # Deal with subdirs recursively
            nfile, ndir = add_files_in_dir(distdir, os.path.join(pkgdir, child), nfile, ndir, output, indent + "  ")

        # os.walk is recursive by default but we do not want this so break out after first listing
        break
    output.write('%s</Directory>\n' % indent)
    return nfile, ndir

def create_wxs(name, plugin_name, distdir, version_str, wxs_fname):
    """
    Create the WXS file for WIX toolset to create the MSI
    """
    formatting_values = {
        "name" : name,
        "version_str" : version_str.replace("-", "."),
        "upgrade_guid" : get_guid('%s/upgrade'),
        "menu_guid" : get_guid('%s/menu' % name),
        "regkeys_guid" : get_guid('%s/regkeys' % name),
    }
    
    output = StringIO()
    nfile, ndir = add_files_in_dir(distdir, plugin_name, 1, 1, output, "  " * 8)
    formatting_values["dist_files"] = output.getvalue()

    output = StringIO()
    for n in range(nfile-1):
        output.write('         <ComponentRef Id="Component%i"/>\n' % (n+1))
    formatting_values["features"] = output.getvalue()

    output = open(wxs_fname, 'w')
    output.write(WXS_TEMPLATE % formatting_values)
    output.close()

def convert_licence(txt_fname, rtf_fname):
    f = open(txt_fname, "r")
    txt = "\\line ".join(f.readlines())
    f.close()
    f = open(rtf_fname, "w")
    f.write(RTF_TEMPLATE % txt)
    f.close()

def create_msi(name, plugin_name, distdir, pkgdir, version_str, version_str_display=None):
    """
    Create the MSI itself using WIX toolset
    """
    if version_str_display == None:
        version_str_display = version_str

    convert_licence(os.path.join(pkgdir, os.pardir, "licence.md"), os.path.join(pkgdir, "licence.rtf"))

    msidir = os.path.join(pkgdir, MSI_SUBDIR)
    shutil.rmtree(msidir, ignore_errors=True)
    os.makedirs(msidir)
    wxs_fname = os.path.join(msidir, "%s.wxs" % name)
    obj_fname = os.path.join(msidir, "%s.wixobj" % name)
    msi_fname = os.path.join(msidir, "%s-%s.msi" % (name, version_str_display))
    create_wxs(name, plugin_name, distdir, version_str, wxs_fname)
    
    os.system('"%s/candle.exe" %s -out %s >>msi.out 2>&1' % (WIXDIR, wxs_fname, obj_fname))
    os.system('"%s/light.exe" %s -out %s -ext WixUIExtension >>msi.out 2>&1' % (WIXDIR, obj_fname, msi_fname))
    shutil.move(msi_fname, distdir)
