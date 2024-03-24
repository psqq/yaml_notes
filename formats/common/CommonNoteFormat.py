from abc import ABC, abstractmethod
 
 
class CommonNoteFormat(ABC):
    def __init__(self):
        from formats.common.NoteAst import Note
        self.fullText = ''
        self.params = dict()
        self.text = ""
        self.noteNode = Note()

    @abstractmethod
    def parse(self, s: str):
        raise NotImplemented()

    @abstractmethod
    def get_default_file_extension(self) -> str:
        raise NotImplemented()

    @abstractmethod
    def from_text(self, s: str):
        raise NotImplemented()

    @abstractmethod
    def to_text(self, params: dict, text: str):
        raise NotImplemented()

