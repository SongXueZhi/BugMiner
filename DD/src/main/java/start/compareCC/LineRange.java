package start.compareCC;

/**
 * @author lsn
 * @date 2023/4/18 6:51 PM
 */
public class LineRange {
    private int startLine;
    private int endLine;

    public LineRange(int startLine, int endLine) {
        this.startLine = startLine;
        this.endLine = endLine;
    }

    public int getStartLine() {
        return startLine;
    }

    public int getEndLine() {
        return endLine;
    }

    @Override
    public String toString() {
        return startLine + "-" + endLine;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (!(obj instanceof LineRange)) {
            return false;
        }

        LineRange other = (LineRange) obj;

        // 比较两个 LineRange 对象的 start 和 end 属性是否相同
        return startLine == other.startLine && endLine == other.endLine;
    }
}
