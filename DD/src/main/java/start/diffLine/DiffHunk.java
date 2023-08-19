package start.diffLine;

/**
 * @author lsn
 * @date 2023/4/17 6:29 PM
 */
public class DiffHunk {
    String hunkName;
    int insertNum;
    int deleteNum;

    public String getHunkName() {
        return hunkName;
    }

    public void setHunkName(String hunkName) {
        this.hunkName = hunkName;
    }

    public int getInsertNum() {
        return insertNum;
    }

    public void setInsertNum(int insertNum) {
        this.insertNum = insertNum;
    }

    public int getDeleteNum() {
        return deleteNum;
    }

    public void setDeleteNum(int deleteNum) {
        this.deleteNum = deleteNum;
    }

    public int getChangeLineNum() {
        return Math.max(insertNum, deleteNum);
    }

}
