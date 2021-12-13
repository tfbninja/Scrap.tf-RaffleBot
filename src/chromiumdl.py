from requests import get
import os
import sys
from io import BytesIO
from zipfile import ZipFile, ZipInfo
import shutil


class ZipFileWithPermissions(ZipFile):
    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath

def getChromiumDownloadUrls(os):
    if (os == "linux"):
        chromium_last_v_url = "https://www.googleapis.com/download/storage/v1/b/" \
                              "chromium-browser-snapshots/o/Linux_x64%2FLAST_CHANGE?alt=media"
        chromium_last_v = get(chromium_last_v_url).text
        chrome_driver_url = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F" + \
                            chromium_last_v + "%2Fchromedriver_linux64.zip?&alt=media"
        chromium_url = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F" + \
                       chromium_last_v + "%2Fchrome-linux.zip?alt=media"

    elif (os == "win32"):
        chromium_last_v_url = "https://www.googleapis.com/download/storage/v1/b/" \
                              "chromium-browser-snapshots/o/Win%2FLAST_CHANGE?&alt=media"
        chromium_last_v = get(chromium_last_v_url).text
        chrome_driver_url = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win%2F" + \
                            chromium_last_v + "%2Fchromedriver_win32.zip?&alt=media"
        chromium_url = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Win%2F" + \
                       chromium_last_v + "%2Fchrome-win.zip?alt=media"

    return chrome_driver_url, chromium_url


def downloadArchiveToMemory(url):
    data = get(url).content
    zip = ZipFileWithPermissions(BytesIO(data))
    return zip;


def fileLocations(path):
    if sys.platform == 'win32':
        webdriver_path = os.path.join(path, 'chromium', 'chromedriver_win32', 'chromedriver.exe')
        chromium_path = os.path.join(path, 'chromium', 'chrome-win', 'chrome.exe')
    elif sys.platform == 'linux':
        webdriver_path = os.path.join(path, 'chromium', 'chromedriver_linux64', 'chromedriver')
        chromium_path = os.path.join(path, 'chromium', 'chrome-linux', 'chrome')
    return webdriver_path, chromium_path


def chromiumdl(path, removeold=False):
    chromium_path = os.path.join(path, 'chromium')
    if os.path.isdir(chromium_path):
        if removeold:
            shutil.rmtree(chromium_path)
        else:
            return fileLocations(path)
    os.mkdir(chromium_path)
    operating_system = sys.platform
    chrome_driver_url, chromium_url = getChromiumDownloadUrls(operating_system)
    print("Detected OS: " + sys.platform)
    print("Downloading Chromium")
    chromiumzip = downloadArchiveToMemory(chromium_url)
    print("Chromium finished downloading")
    print("Downloading Chromedriver")
    chromedriverzip = downloadArchiveToMemory(chrome_driver_url)
    print("Chromedriver finished downloading")
    print("Extracting Chromium")
    chromiumzip.extractall(chromium_path)
    print("Chromium extracted")
    print("Extracting Chromedriver")
    chromedriverzip.extractall(chromium_path)
    print("Chromedriver extracted")
    print("Done")
    return fileLocations(path)


if __name__ == "__main__":
    path = os.path.abspath(os.path.dirname(sys.argv[0]))
    chromiumdl()
