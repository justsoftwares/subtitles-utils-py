import typing
from pathlib import Path

import ass


class Utils:
    def __init__(self, file_path: Path, split_by_dubbers=True, put_into_subs=True,
                 output_dir=None, output_filename=None) -> None:
        self.file_path = file_path
        self.split_by_dubbers = split_by_dubbers
        self.put_into_subs = put_into_subs
        self.output_dir = output_dir if output_dir is not None else Path.cwd()
        self.output_filename = output_filename if output_filename is not None else file_path.name
        self._dubbers_docs: dict[str, ass.Document] = dict()
        self._update_paths()

        with open(file_path, encoding='utf_8_sig') as f:
            self.doc = ass.parse(f)

    def _update_paths(self):
        self._output_path = Path(self.output_dir / self.output_filename)
        self._full_path = self._output_path.with_suffix('.full.ass')

    def _save(self, new_file_path, doc: ass.Document) -> None:
        with open(new_file_path, 'w', encoding='utf_8_sig') as f:
            doc.dump_file(f)

    def _get_line_dubber(self, line: ass.Dialogue) -> str | None:
        dubber = 'free'
        if self.put_into_subs:
            line = line.text.split(']', 1)
            if len(line) == 2 and line[0][0] == '[':
                dubber = line[0][1:]
        else:
            dubber = line.name
        return dubber

    def _set_line_dubber(self, event: ass.Dialogue, dubber: str) -> ass.Dialogue:
        if self.put_into_subs:
            event.text = f'[{dubber}] {event.text}'
        else:
            event.name = dubber
        return event

    def _split_dubbers(self) -> dict[str, ass.Document]:
        self._save(self._full_path, self.doc)
        for i, event in enumerate(self.doc.events):
            # Thread(target=self._process_event, args=(event,)).start()
            self._process_event(event)
        return self._dubbers_docs

    def _process_event(self, event):
        if isinstance(event, ass.Dialogue):
            dubber = self._get_line_dubber(event)
            doc = self._dubbers_docs.get(dubber, None)
            if doc is None:
                with open(self._full_path, encoding='utf_8_sig') as f:
                    self._dubbers_docs[dubber] = ass.parse(f)
                self._dubbers_docs[dubber].events.clear()
                fuck_event = ass.Dialogue()
                fuck_event.text = 'FUCK U, REAPER ~ by dimnissv'
                fuck_event.name = 'dimnissv'
                self._dubbers_docs[dubber].events.append(fuck_event)
            self._dubbers_docs[dubber].events.append(event)

    def save(self):
        self._update_paths()
        if self.split_by_dubbers:
            self._split_dubbers()
            for dubber, doc in self._dubbers_docs.items():
                path = self._output_path.with_suffix(f'.{dubber}.ass')
                try:
                    self._save(path, doc)
                except AttributeError as e:
                    ...

    def update_actors(self, actors: dict[str, typing.Iterable[str]]):
        for event in self.doc.events:
            if isinstance(event, ass.Dialogue):
                dubber = [dubber for dubber, dubber_actors in actors.items() if event.name in actors[dubber]]
                dubber = dubber[0] if len(dubber) == 1 else ''
                if dubber:
                    self._set_line_dubber(event, dubber)

    def get_actors(self) -> set[str]:
        actors = set()
        for event in self.doc.events:
            actors.add(event.name)
        return actors

    def check_actors_coverage(self, actors: typing.Iterable) -> set[str]:
        return {actor for actor in self.get_actors() if actor not in actors}
