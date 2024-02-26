from xrdpattern.xrd_types import XrdPatternDB
from xrdpattern.xrd_file_io import FormatSelector

if __name__ == "__main__":
    patterndb = XrdPatternDB()
    patterndb.import_data(dir_path='/home/daniel/data/mirror/local/parsed/Simon_Schweidler_Ben_Breitung_2024_02_23/data/',
                          format_selector=FormatSelector(format_list=['raw']))
    patterndb.export_data_files(target_dir='/home/daniel/OneDrive/Downloads/raw_export')