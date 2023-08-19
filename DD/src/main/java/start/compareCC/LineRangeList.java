package start.compareCC;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * @author lsn
 * @date 2023/4/18 6:55 PM
 */
public class LineRangeList {
    private List<LineRange> lineRanges;

    public LineRangeList() {
        lineRanges = new ArrayList<>();
    }

    public void addLineRange(LineRange range) {
        lineRanges.add(range);
        Collections.sort(lineRanges, new Comparator<LineRange>() {
            @Override
            public int compare(LineRange lineRange1, LineRange lineRange2) {
                // 按照 startLine 的大小进行比较
                return Integer.compare(lineRange1.getStartLine(), lineRange2.getStartLine());
            }
        });
        mergeLineRanges();
    }

    private void mergeLineRanges() {
        // 合并重叠的行号范围
        List<LineRange> mergedRanges = new ArrayList<>();
        for (LineRange range : lineRanges) {
            if (mergedRanges.isEmpty()) {
                mergedRanges.add(range);
            } else {
                LineRange lastRange = mergedRanges.get(mergedRanges.size() - 1);
                if (lastRange.getEndLine() >= range.getStartLine()) {
                    // 如果当前范围与上一个范围重叠，则合并范围
                    lastRange = new LineRange(lastRange.getStartLine(), Math.max(lastRange.getEndLine(), range.getEndLine()));
                    mergedRanges.set(mergedRanges.size() - 1, lastRange);
                } else {
                    // 如果当前范围与上一个范围不重叠，则添加到合并后的列表中
                    mergedRanges.add(range);
                }
            }
        }
        lineRanges = mergedRanges;
    }

    public List<LineRange> getLineRanges() {
        return lineRanges;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("line range: ");
        for (LineRange range : lineRanges) {
            sb.append(range.toString()).append(" ");
        }
        return sb.toString();
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (!(obj instanceof LineRangeList)) {
            return false;
        }

        LineRangeList other = (LineRangeList) obj;

        // 比较两个 LineRangeList 中的 LineRange 对象是否相同
        if (lineRanges == null) {
            return other.lineRanges == null;
        } else {
            return lineRanges.equals(other.lineRanges);
        }
    }

}
