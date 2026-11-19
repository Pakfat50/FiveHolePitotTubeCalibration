import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.Arrays;

/** 受信行を復元し、全サンプルをCSVに記録する。表示履歴だけをリングに保持する。 */
public class Telemetry {
  public static final String HEADER = "dp_total_Pa,dp_aoa_Pa,dp_aos_Pa,temp_total_C,temp_aoa_C,temp_aos_C,yaw_deg,pitch_deg,roll_deg,acc_x_m_s2,acc_y_m_s2,acc_z_m_s2,gyro_x_rad_s,gyro_y_rad_s,gyro_z_rad_s,bmp_temp_C,bmp_pressure_hPa,timestamp_ms";
  public static final int HISTORY_SECONDS = 600;
  private static final int SIZE = (HISTORY_SECONDS + 1) * 100;
  private final long[] times = new long[SIZE];
  private final float[][] pressure = new float[3][SIZE];
  private final StringBuilder line = new StringBuilder();
  private boolean oversized;
  private int next, count;
  private long timestamp = -1, elapsed, lastFlush;
  private float[] latest = new float[17];
  private BufferedWriter writer;
  public volatile Path pending;
  public volatile long received, invalid, written;
  public volatile boolean recording;
  public volatile String error = "";

  public Telemetry() { Arrays.fill(latest, Float.NaN); }

  public synchronized void resetStream() {
    line.setLength(0);
    oversized = false;
    timestamp = -1;
    next = count = 0;
    elapsed = received = invalid = 0;
    Arrays.fill(latest, Float.NaN);
  }

  public synchronized void accept(byte[] bytes, int length) {
    for (int i = 0; i < length; i++) {
      int c = bytes[i] & 255;
      if (c == 10) {
        if (oversized) invalid++;
        else if (line.length() > 0) acceptLine(line.toString());
        oversized = false;
        line.setLength(0);
      } else if (c != 13 && !oversized) {
        if (line.length() == 4096) oversized = true;
        else line.append((char)c);
      }
    }
  }

  private void acceptLine(String row) {
    String[] fields = row.split("\\t", -1);
    if (fields.length != 18) { invalid++; return; }
    long tick;
    float[] values = new float[17];
    try {
      // 一部の出力関数は整数時刻にも .00 を付ける。CSVでは元表記を保持する。
      tick = new java.math.BigDecimal(fields[17].trim()).longValueExact();
      if (tick < 0 || tick > 0xffffffffL) throw new NumberFormatException();
    } catch (ArithmeticException | NumberFormatException ex) { invalid++; return; }
    for (int i = 0; i < values.length; i++) {
      try { values[i] = Float.parseFloat(fields[i].trim()); }
      catch (NumberFormatException ex) { values[i] = Float.NaN; }
    }
    if (timestamp >= 0) {
      long delta = (tick - timestamp) & 0xffffffffL;
      if (delta > HISTORY_SECONDS * 1000L) count = 0; // 再起動、または表示窓を超える中断
      elapsed += delta;
    }
    timestamp = tick;
    latest = values;
    times[next] = elapsed;
    for (int i = 0; i < 3; i++) pressure[i][next] = values[i];
    next = (next + 1) % SIZE;
    count = Math.min(count + 1, SIZE);
    received++;
    if (recording) {
      try {
        for (int i = 0; i < fields.length; i++) {
          if (i > 0) writer.write(',');
          String f = fields[i];
          if (f.indexOf(',') >= 0 || f.indexOf('"') >= 0)
            writer.write("\"" + f.replace("\"", "\"\"") + "\"");
          else writer.write(f);
        }
        writer.write("\r\n");
        written++;
        if (System.nanoTime() - lastFlush >= 1000000000L) {
          writer.flush();
          lastFlush = System.nanoTime();
        }
      } catch (IOException ex) { error = "記録エラー: " + ex.getMessage(); stop(); }
    }
  }

  public synchronized void start() throws IOException {
    if (pending != null) throw new IOException("先に現在のログを保存してください。");
    Path path = Files.createTempFile("AirDataMonitor-", ".csv");
    try {
      writer = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
      writer.write(HEADER + "\r\n");
      writer.flush();
    } catch (IOException ex) {
      if (writer != null) writer.close();
      Files.deleteIfExists(path);
      throw ex;
    }
    written = 0;
    error = "";
    lastFlush = System.nanoTime();
    pending = path;
    recording = true;
  }

  public synchronized void stop() {
    recording = false;
    if (writer == null) return;
    try { writer.close(); }
    catch (IOException ex) { error = "記録エラー: " + ex.getMessage(); }
    writer = null;
  }

  /** 一時コピーが完成してから置換し、キャンセル・保存失敗時は元ログを保持する。 */
  public void save(Path target) throws IOException {
    Path source;
    synchronized (this) {
      if (recording || pending == null) throw new IOException("記録を停止してください。");
      source = pending;
    }
    target = target.toAbsolutePath();
    if (source.equals(target.normalize()) || (Files.exists(target) && Files.isSameFile(source,target)))
      throw new IOException("一時ログとは別の保存先を選んでください。");
    Path stage = Files.createTempFile(target.getParent(), ".airdata-", ".part");
    try {
      Files.copy(source, stage, StandardCopyOption.REPLACE_EXISTING);
      try { Files.move(stage, target, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
      catch (AtomicMoveNotSupportedException ex) { Files.move(stage, target, StandardCopyOption.REPLACE_EXISTING); }
      Files.delete(source);
      synchronized (this) { pending = null; }
    } finally { Files.deleteIfExists(stage); }
  }

  public static class View {
    public float[] current;
    public long tick;
    public int fromSecond, toSecond;
    public long[] ageMs;
    public float[][] dp;
  }

  private int firstAtOrAfter(int oldest, long target) {
    int lo = 0, hi = count;
    while (lo < hi) {
      int mid = (lo + hi) >>> 1;
      if (times[(oldest + mid) % SIZE] < target) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }

  public synchronized View snapshot(int fromSecond, int toSecond) {
    View v = new View();
    v.current = latest.clone();
    v.tick = timestamp;
    int first = (next - count + SIZE) % SIZE;
    v.fromSecond = fromSecond;
    v.toSecond = toSecond;
    int begin = firstAtOrAfter(first, elapsed + fromSecond * 1000L);
    int end = firstAtOrAfter(first, elapsed + toSecond * 1000L + 1);
    int n = end - begin;
    first = (first + begin) % SIZE;
    v.ageMs = new long[n];
    v.dp = new float[3][n];
    for (int i = 0; i < n; i++) {
      int j = (first + i) % SIZE;
      v.ageMs[i] = times[j] - elapsed;
      for (int k = 0; k < 3; k++) v.dp[k][i] = pressure[k][j];
    }
    return v;
  }
}
