import numpy as np

from pypulseq.event_lib import EventLibrary


def read(self, path, **kwargs):
    """
    Reads .seq file from path, and constructs a Sequence object from the file.

    Parameters
    ----------
    path : str
        Path of .seq file to be read.
    """

    detect_rf_use = True if 'detect_rf_use' in kwargs else False

    input_file = open(path, 'r')
    self.shape_library = EventLibrary()
    self.rf_library = EventLibrary()
    self.grad_library = EventLibrary()
    self.adc_library = EventLibrary()
    self.delay_library = EventLibrary()
    self.block_events = {}
    self.rf_raster_time = self.system.rf_raster_time
    self.grad_raster_time = self.system.grad_raster_time
    self.definitions = {}

    while True:
        section = skip_comments(input_file)
        if section == -1:
            break

        if section == '[DEFINITIONS]':
            self.definitions = read_definitions(input_file)
        elif section == '[VERSION]':
            version_major, version_minor, version_revision = read_version(input_file)
            if version_major != self.version_major or version_minor != self.version_minor or version_revision != self.version_revision:
                raise Exception(
                    f'Unsupported version: {version_major, version_minor, version_revision}. '
                    f'Expected: {self.version_major, self.version_minor, self.version_revision}')
        elif section == '[BLOCKS]':
            self.block_events = read_blocks(input_file)
        elif section == '[rf]':
            self.rf_library = read_events(input_file, [1, 1, 1, 1e-6, 1, 1])
        elif section == '[GRAD]':
            self.grad_library = read_events(input_file, [1, 1, 1e-6], 'g', self.grad_library)
        elif section == '[TRAP]':
            self.grad_library = read_events(input_file, [1, 1e-6, 1e-6, 1e-6, 1e-6], 't', self.grad_library)
        elif section == '[ADC]':
            self.adc_library = read_events(input_file, [1, 1e-9, 1e-6, 1, 1])
        elif section == '[DELAYS]':
            self.delay_library = read_events(input_file, 1e-6)
        elif section == '[SHAPES]':
            self.shape_library = read_shapes(input_file)
        else:
            raise ValueError(f'Unknown section code: {section}')

    if detect_rf_use:
        for k in self.rf_library.keys():
            lib_data = self.rf_library.data[k]
            rf = self.rf_from_lib_data(lib_data)
            flip_deg = abs(np.sum(rf.signal)) * rf.t[0] * 360
            if len(lib_data) < 9:
                if flip_deg <= 90:
                    lib_data[8] = 0
                else:
                    lib_data[8] = 2
                self.rf_library.data[k] = lib_data


def read_definitions(input_file):
    definitions = dict()
    line = strip_line(input_file)
    while line != '' and line[0] != '#':
        tok = line.split(' ')
        if not any([x.isalpha() for x in tok[1:]]):
            definitions[tok[0]] = np.array(tok[1:], dtype=float)
        else:
            definitions[tok[0]] = tok[1:]
        line = strip_line(input_file)

    return definitions


def read_version(input_file):
    line = strip_line(input_file)
    while line != '' and line[0] != '#':
        tok = line.split(' ')
        if tok[0] == 'major':
            major = np.array(tok[1:], dtype=float)
        elif tok[0] == 'minor':
            minor = np.array(tok[1:], dtype=float)
        elif tok[0] == 'revision':
            revision = np.array(tok[1:], dtype=float)
        line = strip_line(input_file)

    return major, minor, revision


def read_blocks(input_file):
    """
    Read Blocks from .seq file. Blocks are single lines under the '[BLOCKS]' header in the .seq file.

    Parameters
    ----------
    input_file : file
        .seq file to be read.

    Returns
    -------
    block_events : dict
        Key-value mapping of Block ID and Event ID.
    """

    line = strip_line(input_file)

    event_table = dict()
    while line != '' and line != '#':
        block_events = np.fromstring(line, dtype=int, sep=' ')
        event_table[block_events[0]] = block_events[1:]
        line = strip_line(input_file)

    return event_table


def read_events(input_file, scale, type=None, event_library=None):
    scale = 1 if scale is None else scale
    event_library = event_library if event_library is not None else EventLibrary()

    line = strip_line(input_file)

    while line != '' and line != '#':
        data = np.fromstring(line, dtype=float, sep=' ')
        id = data[0]
        data = data[1:] * scale
        if type is None:
            event_library.insert(key_id=id, new_data=data)
        else:
            event_library.insert(key_id=id, new_data=data, data_type=type)
        line = strip_line(input_file)

    return event_library


def read_shapes(input_file):
    shape_library = EventLibrary()

    line = skip_comments(input_file)

    while line != -1 and (line != '' or line[0:8] == 'shape_id'):
        tok = line.split(' ')
        id = int(tok[1])
        line = skip_comments(input_file)
        tok = line.split(' ')
        num_samples = int(tok[1])
        data = []
        line = skip_comments(input_file)
        while line != '' and line != '#':
            data.append(float(line))
            line = strip_line(input_file)
        line = skip_comments(input_file)
        data.insert(0, num_samples)
        data = np.asarray(data)
        shape_library.insert(key_id=id, new_data=data)
    return shape_library


def skip_comments(input_file):
    """
    Skip one '#' comment in .seq file.

    Parameters
    ----------
    input_file : file
        .seq file to be read.

    Returns
    -------
    line : str
        First line in input_file after skipping one '#' comment block.
        Note: File pointer is remembered, so successive calls work as expected.
    """

    line = strip_line(input_file)

    while line != -1 and (line == '' or line[0] == '#'):
        line = strip_line(input_file)

    return line


def strip_line(input_file):
    """
    Remove spaces, newline whitespace and return line.

    Parameters
    ----------
    input_file : file
        .seq file to be read.

    Returns
    -------
    line : str
        First line in input_file after removing spaces and newline whitespaces.
        Note: File pointer is remembered, so successive calls work as expected.
    """
    line = input_file.readline()  # If line is an empty string, end of the file has been reached
    return line.strip() if line != '' else -1
