import mock_catalyst
from mock_catalyst import EndOfApplication
# from vocollect_lut_odr_test.mock_server import MockServer, BOTH_SERVERS
from main import main
# import sys
# voice.log_message("Agora caiu no HTTPODR")  
mock_catalyst.environment_properties['SwVersion.Locale'] = 'pt_BR'

# 
# def log_message(msg):
#     if mock_catalyst.use_stdin_stdout:
#         sys.stdout.write('>> ' + msg + '\n')
#         sys.stdout.flush()        
# sys.modules['voice'].log_message = log_message

# mock_catalyst.post_dialog_responses('ready!',
#                                    '123!', 
#                                    '3!',
#                                    'yes',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    '290!',
#                                    '10!',
#                                    '11!',
#                                    '1!',
#                                    'yes!',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    'sign off!',
#                                    'yes!'
#                                    )


# mock_catalyst.post_dialog_responses('ready!',
#                                    '123!', 
#                                    '3!',
#                                    'yes',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    'ready!',
#                                    '290!',
#                                    '10!',
#                                    'short!',
#                                    'yes!',
#                                    '5!',
#                                    'yes!',
#                                     'yes!'
#                                    )


try:
    main()
except EndOfApplication as err:
    print('Application ended')
    
# ms.stop_server(BOTH_SERVERS)


#Sample test case creation
#from CreateTestFile import CreateTestFile
#test = CreateTestFile('Sample', ms)
#path = '' #should end with slash if specified (i.e. test\functional_tests\Selection_tests\)
#test.write_test_to_file(path)
