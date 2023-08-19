package start;

import java.util.LinkedList;
import java.util.List;

/**
 * @Author: sxz
 * @Date: 2022/12/26/19:03
 * @Description:
 */
public class Regression {

    private String id;
    private String project_full_name;
    private String bfc;
    private String buggy;
    private String bic;
    private String work;
    private String errorType;

    private Revision bfcRev;
    private Revision buggyRev;
    private Revision bicRev;
    private Revision workRev;

    private String testCaseString;
    private List<String> testCaseList = new LinkedList<>();

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getProject_full_name() {
        return project_full_name;
    }

    public void setProject_full_name(String project_full_name) {
        this.project_full_name = project_full_name;
    }

    public String getBfc() {
        return bfc;
    }

    public void setBfc(String bfc) {
        this.bfc = bfc;
    }

    public String getBuggy() {
        return buggy;
    }

    public void setBuggy(String buggy) {
        this.buggy = buggy;
    }

    public String getBic() {
        return bic;
    }

    public void setBic(String bic) {
        this.bic = bic;
    }

    public String getWork() {
        return work;
    }

    public void setWork(String work) {
        this.work = work;
    }

    public String getErrorType() {
        return errorType;
    }

    public void setErrorType(String errorType) {
        this.errorType = errorType;
    }

    public String getTestCaseString() {
        return testCaseString;
    }

    public void setTestCaseString(String testCaseString) {
        this.testCaseString = testCaseString;
    }

    public List<String> getTestCaseList() {
        return testCaseList;
    }

    public void setTestCaseList(List<String> testCaseList) {
        this.testCaseList = testCaseList;
    }

    public Revision getBfcRev() {
        return bfcRev;
    }

    public void setBfcRev(Revision bfcRev) {
        this.bfcRev = bfcRev;
    }

    public Revision getBuggyRev() {
        return buggyRev;
    }

    public void setBuggyRev(Revision buggyRev) {
        this.buggyRev = buggyRev;
    }

    public Revision getBicRev() {
        return bicRev;
    }

    public void setBicRev(Revision bicRev) {
        this.bicRev = bicRev;
    }

    public Revision getWorkRev() {
        return workRev;
    }

    public void setWorkRev(Revision workRev) {
        this.workRev = workRev;
    }
}
