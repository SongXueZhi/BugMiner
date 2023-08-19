package start;

import java.io.File;
import java.util.Arrays;
import java.util.StringJoiner;

/**
 * @Author: sxz
 * @Date: 2022/12/26/19:02
 * @Description:
 */
public class RegCleaner {
    private final String MVN_COMPILE = "mvn compile test-compile";
    private final String GRADLE_COMPILE = "./gradlew compileJava compileTestJava";
    private final String MVN_TEST = "mvn test -Dtest=";
    private final String GRADLE_TEST = "./gradlew test --tests ";

    // 针对bfc 测试10次 看看是不是PASS
    // 针对buggy 测试10次，看看是不是FAL
    // 针对bic 测试10次，看看是不是FAL
    // 针对work 测试10次，看看是不是PASS
    void clean(Regression regression) {
        String testString = regression.getTestCaseString();
        String[] testCaseArray = testString.split(";");
        StringJoiner newTestCase = new StringJoiner(";");
        StringJoiner msg = new StringJoiner(";");
        int isDirty =1;
        for (String testCase : testCaseArray) {
            CleanResult cleanResult = test(regression, testCase);
            if (cleanResult.isSuccess()){
                isDirty =0;
                newTestCase.add(testCase);
            }
            msg.add(cleanResult.toString());
        }
        String sql  = "update regressions_all set is_dirty="+isDirty+", testcase1='"+newTestCase.toString()+"', " +
                "msg='"+msg.toString()+"', is_clean=1 where id="+regression.getId();
        MysqlManager.executeUpdate(sql);
        System.out.println(regression.getId()+"--->"+isDirty+"----->"+newTestCase);
        System.out.println(msg);
    }


    CleanResult test(Regression regression, String testCase) {
        CleanResult cleanResult = new CleanResult();

        //对bfc进行编译、测试
        BUILD_TOOL buildTool = defectBuildTool(regression.getBfcRev().getLocalCodeDir());
        String compileCMD = MVN_COMPILE;
        String testCMD = MVN_TEST + testCase;
        if (buildTool == BUILD_TOOL.GRADLEW) {
            compileCMD = GRADLE_COMPILE;
            testCMD = GRADLE_TEST + testCase.replace("#", ".");
        }
        //bfc编译成功
        if (new Executor().setDirectory(regression.getBfcRev().getLocalCodeDir()).execBuildWithResult(compileCMD)) {
            Executor executor =  new Executor().setDirectory(regression.getBfcRev().getLocalCodeDir());
            TestResult.STATUS status = null;
            int testTrueNum = 0;
            //检测测试用例的状态以及稳定性
            for (int i = 0; i<10; i++){
                status = executor.execTestWithResult(testCMD);
                if (status == TestResult.STATUS.PASS){
                    testTrueNum++;
                }
            }
            TestResult testResult = null;
            //bfc必须稳定的PASS
            if (testTrueNum != 10){
                //99 测试用例不稳定
                testResult = new TestResult("99","bfc-"+status.name()+ " " + testCase);
            }
            if (testTrueNum == 0){
                //101 bfc测试FAL
                testResult = new TestResult("101", "bfc-" + status.name() + " " + testCase);
            }
            if (testTrueNum != 10){ //不稳定或者FAL算失败处理
                cleanResult.setSuccess(false);
                cleanResult.setTestResult(testResult);
                return cleanResult;
            }
        } else {//bfc 编译失败处理
            cleanResult.setSuccess(false);
            cleanResult.setTestResult(new TestResult("100", "bfc-CE" + " " + testCase));
            return cleanResult;
        }

        //对buggy进行编译、测试
        //检测编译方式
        buildTool = defectBuildTool(regression.getBuggyRev().getLocalCodeDir());
        if (buildTool == BUILD_TOOL.GRADLEW) {
            compileCMD = GRADLE_COMPILE;
            testCMD = GRADLE_TEST + testCase.replace("#", ".");
        } else {
            compileCMD = MVN_COMPILE;
            testCMD = MVN_TEST + testCase;
        }

        //buggy编译成功
        if (new Executor().setDirectory(regression.getBuggyRev().getLocalCodeDir()).execBuildWithResult(compileCMD)) {
            Executor executor =  new Executor().setDirectory(regression.getBuggyRev().getLocalCodeDir());
            TestResult.STATUS status = null;
            int testTrueNum = 0;
            //检测测试用例的状态以及稳定性
            for (int i = 0; i<10; i++){
                status = executor.execTestWithResult(testCMD);
                if (status == TestResult.STATUS.FAIL){
                    testTrueNum++;
                }
            }
            //buggy 允许测试不稳定
            if (testTrueNum>0 && testTrueNum<10){
                cleanResult.setStable(false);
            }
            //但不允许测试全部不是FAL
            if (testTrueNum == 0){
                cleanResult.setSuccess(false);
                cleanResult.setTestResult(new TestResult("101", "buggy-" + status.name() + " " + testCase));
                return cleanResult;
            }
        } else { //buggy编译失败处理
            cleanResult.setSuccess(false);
            cleanResult.setTestResult(new TestResult("100", "buggy-CE" + " " + testCase));
            return cleanResult;
        }

        //对bic进行编译、测试
        //检测编译方式
        buildTool = defectBuildTool(regression.getBicRev().getLocalCodeDir());
        if (buildTool == BUILD_TOOL.GRADLEW) {
            compileCMD = GRADLE_COMPILE;
            testCMD = GRADLE_TEST + testCase.replace("#", ".");
        } else {
            compileCMD = MVN_COMPILE;
            testCMD = MVN_TEST + testCase;
        }
        //bic编译成功
        if (new Executor().setDirectory(regression.getBicRev().getLocalCodeDir()).execBuildWithResult(compileCMD)) {
            Executor executor =  new Executor().setDirectory(regression.getBicRev().getLocalCodeDir());
            TestResult.STATUS status = null;
            int testTrueNum = 0;
            //检测测试用例的状态以及稳定性
            for (int i = 0; i<10; i++){
                status = executor.execTestWithResult(testCMD);
                if (status == TestResult.STATUS.FAIL){
                    testTrueNum++;
                }
            }
            // bic 也允许测试不稳定
            if (testTrueNum>0 && testTrueNum<10){
                cleanResult.setStable(false);
            }
            //但不允许测试全部不是FAL
            if (testTrueNum == 0){
                cleanResult.setSuccess(false);
                cleanResult.setTestResult(new TestResult("101", "bic-" + status.name() + " " + testCase));
                return cleanResult;
            }
        } else { //bic编译失败处理
            cleanResult.setSuccess(false);
            cleanResult.setTestResult(new TestResult("100", "bic-CE" + " " + testCase));
            return cleanResult;
        }

        //对work进行编译、测试
        //检测编译方式
        buildTool = defectBuildTool(regression.getWorkRev().getLocalCodeDir());
        if (buildTool == BUILD_TOOL.GRADLEW) {
            compileCMD = GRADLE_COMPILE;
            testCMD = GRADLE_TEST + testCase.replace("#", ".");
        } else {
            compileCMD = MVN_COMPILE;
            testCMD = MVN_TEST + testCase;
        }
        //work编译成功
        if (new Executor().setDirectory(regression.getWorkRev().getLocalCodeDir()).execBuildWithResult(compileCMD)) {
            Executor executor =  new Executor().setDirectory(regression.getWorkRev().getLocalCodeDir());
            TestResult.STATUS status = null;
            int testTrueNum = 0;
            //检测测试用例的状态以及稳定性
            for (int i = 0; i<10; i++){
                status = executor.execTestWithResult(testCMD);
                if (status == TestResult.STATUS.PASS){
                    testTrueNum++;
                }
            }
            TestResult testResult = null;
            //work必须稳定的PASS
            if (testTrueNum != 10){
                //99 测试用例不稳定
                testResult = new TestResult("99","bfc-"+status.name()+ " " + testCase);
            }
            if (testTrueNum == 0){
                //101 work测试FAL
                testResult = new TestResult("101", "bfc-" + status.name() + " " + testCase);
            }
            if (testTrueNum != 10){ //不稳定或者FAL算失败处理
                cleanResult.setSuccess(false);
                cleanResult.setTestResult(testResult);
                return cleanResult;
            }
        } else { //work编译失败处理
            cleanResult.setSuccess(false);
            cleanResult.setTestResult(new TestResult("100", "work-CE" + " " + testCase));
            return cleanResult;
        }
        cleanResult.setSuccess(true);
        return cleanResult;
    }

    BUILD_TOOL defectBuildTool(File codeDir) {
        String[] childs = codeDir.list();
        boolean isMvn = Arrays.stream(childs).filter(name -> name.equals("pom.xml")).findAny().isPresent();
        if (isMvn) {
            return BUILD_TOOL.MVN;
        } else {
            return BUILD_TOOL.GRADLEW;
        }
    }

    enum BUILD_TOOL {
        MVN,
        GRADLEW;
    }
}
