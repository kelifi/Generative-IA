class Singleton:
    def __init__(self, cls):
        self._cls = cls

    def Instance(self):
        try:
            return self._instance

        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._cls)


@Singleton
class Streaming_media_object:
    def __init__(self):
        self.video_path, self.file_download, self.audio_file_path, self.file_size = (None, None, None, None)

    def __str__(self):
        return 'Database connection object'


