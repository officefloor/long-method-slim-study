package example;

import java.util.List;

public class Examples {

    // Example A: guard clauses. Stuck under single-exit extraction: every cut contains a return.
    // The injection split: two functions, nothing carried; each return is a flow to the end.
    public String describe(Order order, Customer customer, Catalog catalog) {
        // FUNCTION check: a return ends the flow, else next
        if (order == null) {
            return "no order";
        }
        if (order.getLines().isEmpty()) {
            return "empty order";
        }
        if (customer == null) {
            return "no customer";
        }
        if (!customer.isActive()) {
            return "inactive customer";
        }
        // END FUNCTION: passes nothing on
        // FUNCTION price: declares nothing
        int total = catalog.totalOf(order.getLines());
        if (total == 0) {
            return "free";
        }
        int discount = customer.discountFor(total);
        if (discount > total) {
            return "invalid discount";
        }
        int due = total - discount;
        String currency = customer.getCurrency();
        if (currency == null) {
            return "no currency";
        }
        String note = customer.noteFor(due);
        if (note == null) {
            return currency + " " + due;
        }
        return currency + " " + due + " (" + note + ")";
        // END FUNCTION: returns the String
    }

    // Example B: a pipeline. Three stages; the first hands two values on, and a parameter is read throughout.
    // SinewSlim: the two loops extracted (EXTRACT). The combined split: two functions (FUNCTION). The injection split alone: three (INJECTION).
    public Report build(List<String> rows, Options options) {
        // FUNCTION parse: declares nothing
        // INJECTION prepare: declares nothing
        List<Record> records = new java.util.ArrayList<>();
        int skipped = 0;
        // END INJECTION: passes on records
        // INJECTION tally: declares records
        // EXTRACT parseRows(rows, options, records)
        for (String row : rows) {
            String[] cells = row.split(options.separator());
            if (cells.length < 3) {
                skipped++;
                continue;
            }
            Record record = new Record();
            record.setKey(cells[0].trim());
            record.setValue(Integer.parseInt(cells[1].trim()));
            record.setUnit(cells[2].trim());
            record.setSource(options.source());
            records.add(record);
        }
        // END EXTRACT: returns skipped
        // END FUNCTION: passes on records, skipped
        // FUNCTION summarise: declares records, skipped
        Summary summary = new Summary();
        // EXTRACT summarise(options, records, summary)
        for (Record record : records) {
            if (record.getValue() < options.minimum()) {
                summary.addInvalid(record.getKey());
                continue;
            }
            summary.addTotal(record.getValue());
            summary.addUnit(record.getUnit());
            summary.addSource(record.getSource());
            summary.incrementCount();
        }
        // END EXTRACT: returns nothing
        summary.setSkipped(skipped);
        // END INJECTION: passes on summary
        // INJECTION report: declares summary
        Report report = new Report();
        report.setTitle(options.title() + ": " + summary.getCount() + " records");
        report.setTotal(summary.getTotal());
        report.setUnits(summary.getUnits());
        report.setSources(summary.getSources());
        report.setInvalid(summary.getInvalid());
        report.setSkipped(summary.getSkipped());
        report.setGenerated(System.currentTimeMillis());
        report.setFormat(options.format());
        report.finish();
        return report;
        // END INJECTION: returns report
        // END FUNCTION: returns report
    }

    interface Order { List<Line> getLines(); }
    interface Line { String getSku(); int getQuantity(); }
    interface Customer { boolean isActive(); int discountFor(int total); String getCurrency(); String noteFor(int due); }
    interface Catalog { int totalOf(List<Line> lines); }
    interface Options { String separator(); String source(); int minimum(); String title(); String format(); }
    static class Record { String k; int v; String u; String n; boolean valid; String s; int seq;
        void setKey(String x){k=x;} void setValue(int x){v=x;} void setUnit(String x){u=x;} void setNote(String x){n=x;}
        void setValid(boolean x){valid=x;} void setSource(String x){s=x;} void setSequence(int x){seq=x;}
        String getKey(){return k;} int getValue(){return v;} String getUnit(){return u;} String getNote(){return n;}
        boolean isValid(){return valid;} String getSource(){return s;} int getSequence(){return seq;} }
    static class Summary { int count, total, skipped; void setSkipped(int s){skipped=s;} int getSkipped(){return skipped;} void addInvalid(String k){} void addTotal(int v){total+=v;} void addUnit(String u){}
        void addNote(String n){} void addSource(String s){} void markSequence(int s){} void incrementCount(){count++;}
        int getCount(){return count;} int getTotal(){return total;} List<String> getUnits(){return null;} List<String> getNotes(){return null;}
        List<String> getSources(){return null;} List<String> getInvalid(){return null;} int getSequence(){return 0;} }
    static class Report { void setTitle(String t){} void setTotal(int t){} void setUnits(List<String> u){} void setNotes(List<String> n){}
        void setSources(List<String> s){} void setInvalid(List<String> i){} void setSequence(int s){} void setGenerated(long g){}
        void setFormat(String f){} void setSkipped(int s){} void finish(){} }
}
