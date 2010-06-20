import hashlib

class StaticFileHandler(object):
    def __init__(self, path, base_url):
        self.path = path
        self.hashes = {}
        self.sizes = {}
        self.base_url = base_url

    def url(self, url):
        if url not in self.hashes:
            data = open(self.path + '/' + url).read()
            self.hashes[url] = hashlib.md5(data).hexdigest()[:5]
        return self.base_url + url + '?v=' + self.hashes[url]

    def img_size(self, url):
        if url not in self.sizes:
            import Image
            fobj = open(self.path + '/' + url)
            self.sizes[url] = Image.open(fobj).size
        return self.sizes[url]
