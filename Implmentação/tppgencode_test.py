import tpplex
import tppparser
import tppsema
import subprocess
import os, fnmatch

def execute_test(input_file):
    path_file = 'tests/' + input_file
    process = subprocess.Popen(['python', 'tppgencode.py', path_file],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout, stderr

    output_file = open(path_file + ".out", "r")

    #read whole file to a string
    expected_output = output_file.read()

    output_file.close()

    print(stdout)
    print(expected_output)

    return stdout.decode("utf-8") == expected_output

#def testes():
#    for file in fnmatch.filter(os.listdir('tests'), '*.tpp'):
#        assert execute_test(file) == True

def test_001():
    assert execute_test("gencode-001.tpp") == True

def test_002():
    assert execute_test("gencode-002.tpp") == True

def test_003():
    assert execute_test("gencode-003.tpp") == True

def test_004():
    assert execute_test("gencode-004.tpp") == True

def test_005():
    assert execute_test("gencode-005.tpp") == True

def test_006():
    assert execute_test("gencode-006.tpp") == True

def test_007():
    assert execute_test("gencode-007.tpp") == True

def test_008():
    assert execute_test("gencode-008.tpp") == True

def test_009():
    assert execute_test("gencode-009.tpp") == True

def test_010():
    assert execute_test("gencode-010.tpp") == True

def test_011():
    assert execute_test("gencode-011.tpp") == True

def test_012():
    assert execute_test("gencode-012.tpp") == True

def test_013():
    assert execute_test("gencode-013.tpp") == True

def test_014():
    assert execute_test("gencode-014.tpp") == True

def test_015():
    assert execute_test("gencode-015.tpp") == True

def test_016():
    assert execute_test("gencode-016.tpp") == True

def test_017():
    assert execute_test("gencode-017.tpp") == True

def test_018():
    assert execute_test("gencode-018.tpp") == True

def test_019():
    assert execute_test("gencode-019.tpp") == True

def test_020():
    assert execute_test("gencode-020.tpp") == True

def test_021():
    assert execute_test("gencode-021.tpp") == True

def test_022():
    assert execute_test("gencode-022.tpp") == True

def test_023():
    assert execute_test("gencode-023.tpp") == True

def test_024():
    assert execute_test("gencode-024.tpp") == True

def test_025():
    assert execute_test("gencode-025.tpp") == True

def test_026():
    assert execute_test("gencode-026.tpp") == True

def test_027():
    assert execute_test("gencode-027.tpp") == True

def test_028():
    assert execute_test("gencode-028.tpp") == True

def test_029():
    assert execute_test("gencode-029.tpp") == True

def test_030():
    assert execute_test("gencode-030.tpp") == True

def test_031():
    assert execute_test("gencode-031.tpp") == True

def test_032():
    assert execute_test("gencode-032.tpp") == True


