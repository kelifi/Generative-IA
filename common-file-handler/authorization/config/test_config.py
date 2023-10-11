from authorization.models.structures import StreamingFileInDB


class UnitTestFiles:
    STREAMING_FILE_DATA = StreamingFileInDB(id="331007a4-2d5d-4eac-a5bb-4107db076a62",
                                            file_id="f4567ac7-dd2b-4aa4-8fbc-cf0f6e99dc43",
                                            file_temp_path="test_file",
                                            file_creation_time="05-05-2022")
    TEST_TOTAL_DURATION = 100
    TEST_DURATION_LEFT = 50
    TEST_FILE_NAME = "./test_file.wav"
    TEST_FILE_NAME_Exception = "./test_file1.wav"
