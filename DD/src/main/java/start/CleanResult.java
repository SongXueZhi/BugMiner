package start;

/**
 * @Author: sxz
 * @Date: 2023/02/03/23:55
 * @Description:
 */
public class CleanResult {
    private  TestResult testResult;
    private  boolean isSuccess;
    private boolean isStable = true;

    public TestResult getTestResult() {
        return testResult;
    }

    public void setTestResult(TestResult testResult) {
        this.testResult = testResult;
    }

    public boolean isSuccess() {
        return isSuccess;
    }

    public void setSuccess(boolean success) {
        isSuccess = success;
    }

    public boolean isStable() {
        return isStable;
    }

    public void setStable(boolean stable) {
        isStable = stable;
    }

    @Override
    public String toString() {
        return new org.apache.commons.lang3.builder.ToStringBuilder(this)
                .append("testResult", testResult)
                .append("isSuccess", isSuccess)
                .append("isStable", isStable)
                .toString();
    }
}
