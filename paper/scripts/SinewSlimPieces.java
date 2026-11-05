import net.officefloor.sinewslim.core.*;
import net.officefloor.sinewslim.facts.Seam;
import net.officefloor.sinewslim.javaparser.*;
import java.nio.file.*;
import java.util.*;

/** SinewSlim's segmentation of each long method of a file, as JSON: the scan reports its cost, width and
 *  piece count but not the pieces, and the paper names them. Run by scan.sh against the pinned jar. */
public class SinewSlimPieces {
    public static void main(String[] a) throws Exception {
        String src = Files.readString(Path.of(a[0]));
        ParsedFile f = JavaFacts.parse(a[0], src);
        StringBuilder out = new StringBuilder("{\n  \"tool\": \"SinewSlim via " + a[1] + "\",\n  \"methods\": [\n");
        boolean firstM = true;
        for (MethodUnit m : f.methods()) {
            Assessment as = Assessor.DEFAULTS.assess(m.facts());
            if (as.status() == Assessment.Status.UNDER_CAP) continue;
            SlimResult r = as.proposal();
            out.append(firstM ? "" : ",\n").append("    {\"signature\": \"").append(m.signature())
               .append("\", \"status\": \"").append(as.status().name().toLowerCase())
               .append("\", \"feasible\": ").append(r != null && r.feasible());
            if (r != null && r.feasible()) {
                out.append(", \"cost\": ").append(r.cost()).append(", \"width\": ").append(r.width())
                   .append(", \"remainder\": ").append(r.remainder()).append(", \"pieces\": [");
                boolean firstP = true;
                for (Seam s : r.cuts()) {
                    out.append(firstP ? "" : ", ").append("{\"lo\": ").append(s.lo()).append(", \"hi\": ").append(s.hi())
                       .append(", \"inputs\": ").append(json(s.inputs())).append(", \"outputs\": ").append(json(s.outputs()))
                       .append(", \"passed\": ").append(json(s.passed())).append("}");
                    firstP = false;
                }
                out.append("]");
            }
            out.append("}");
            firstM = false;
        }
        out.append("\n  ]\n}\n");
        Files.writeString(Path.of(a[2]), out.toString());
    }

    static String json(List<String> xs) {
        StringJoiner j = new StringJoiner(", ", "[", "]");
        for (String x : xs) j.add("\"" + x + "\"");
        return j.toString();
    }
}
