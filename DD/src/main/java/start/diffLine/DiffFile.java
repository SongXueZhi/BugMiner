package start.diffLine;

import java.util.ArrayList;

/**
 * @author lsn
 * @date 2023/4/17 6:29 PM
 */
public class DiffFile {
    String fileNameA;
    String fileNameB;
    ArrayList<DiffHunk> diffHunks = new ArrayList<>();

    public String getFileNameA() {
        return fileNameA;
    }

    public void setFileNameA(String fileNameA) {
        this.fileNameA = fileNameA;
    }

    public String getFileNameB() {
        return fileNameB;
    }

    public void setFileNameB(String fileNameB) {
        this.fileNameB = fileNameB;
    }


    public ArrayList<DiffHunk> getDiffHunks() {
        return diffHunks;
    }

    public void setDiffHunks(ArrayList<DiffHunk> diffHunks) {
        this.diffHunks = diffHunks;
    }
}
