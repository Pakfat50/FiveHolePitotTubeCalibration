import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

/** AirDataCalibrationの3次係数を、描画用にコピーしたサンプルへ適用する。 */
public final class Calibration {
  private final double[][] terms = new double[3][10];
  public final String filename;

  private Calibration(Path file) { filename = file.getFileName().toString(); }

  public static Calibration load(Path file) throws IOException {
    Calibration result = new Calibration(file);
    boolean[] seen = new boolean[10];
    try (BufferedReader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
      String header = reader.readLine();
      if (header == null) throw new IOException("係数CSVが空です。");
      List<String> columns = Arrays.asList(header.replace("\uFEFF", "").split(",", -1));
      String[] names = {"power_aoa","power_aos","alpha_deg","beta_deg","q_factor"};
      int[] col = new int[names.length];
      for (int i=0; i<names.length; i++) {
        col[i] = columns.indexOf(names[i]);
        if (col[i]<0) throw new IOException("係数CSVに "+names[i]+" がありません。");
      }
      String line;
      while ((line=reader.readLine())!=null) {
        if (line.trim().isEmpty()) continue;
        String[] row=line.split(",",-1);
        if (row.length!=columns.size()) throw new IOException("係数CSVの列数が一致しません。");
        int i=Integer.parseInt(row[col[0]].trim()), j=Integer.parseInt(row[col[1]].trim());
        if (i<0 || j<0 || i>3 || j>3 || i+j>3) throw new IOException("係数の指数が不正です。");
        int degree=i+j, index=degree*(degree+1)/2+j;
        if (seen[index]) throw new IOException("係数の項が重複しています。");
        seen[index]=true;
        for (int k=0; k<3; k++) {
          double value=Double.parseDouble(row[col[k+2]].trim());
          if (!Double.isFinite(value)) throw new IOException("較正係数が有限値ではありません。");
          result.terms[k][index]=value;
        }
      }
    } catch (NumberFormatException ex) { throw new IOException("係数CSVに不正な数値があります。",ex); }
    for (boolean found:seen) if (!found) throw new IOException("較正係数の10項が揃っていません。");
    return result;
  }

  private double polynomial(double[] c,double a,double s) {
    return c[0]+a*(c[1]+a*(c[3]+a*c[6]+s*c[7])+s*(c[4]+s*c[8]))
               +s*(c[2]+s*(c[5]+s*c[9]));
  }

  // 表示順はリファレンス動圧、迎角、横滑り角。配列は描画スナップショットに属する。
  private void estimate(double total,double aoa,double aos,float[] out) {
    if (!(total>0) || !Double.isFinite(total) || !Double.isFinite(aoa) || !Double.isFinite(aos)) {
      Arrays.fill(out,Float.NaN);
      return;
    }
    double a=aoa/total, s=aos/total;
    out[0]=(float)(total*polynomial(terms[2],a,s));
    out[1]=(float)polynomial(terms[0],a,s);
    out[2]=(float)polynomial(terms[1],a,s);
  }

  public static void apply(Telemetry.View view,Calibration model) {
    if (model==null) {
      Arrays.fill(view.current,0,3,Float.NaN);
      for (float[] series:view.dp) Arrays.fill(series,Float.NaN);
      return;
    }
    float[] out=new float[3];
    model.estimate(view.current[0],view.current[1],view.current[2],out);
    System.arraycopy(out,0,view.current,0,3);
    for (int i=0;i<view.ageMs.length;i++) {
      model.estimate(view.dp[0][i],view.dp[1][i],view.dp[2][i],out);
      for(int k=0;k<3;k++) view.dp[k][i]=out[k];
    }
  }
}
