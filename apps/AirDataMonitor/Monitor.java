import processing.core.PApplet;
import processing.serial.Serial;
import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Arrays;
import java.util.Locale;

/** 受信専用スレッドと、描画・ダイアログの責務を分ける。 */
public class Monitor {
  private final PApplet app;
  private final Telemetry data = new Telemetry();
  private final PanelArt rawPanel=new PanelArt(false), calibratedPanel=new PanelArt(true);
  private volatile PanelArt activePanel=rawPanel;
  private volatile Calibration calibration;
  private volatile String port="", message="COMポートを選択してください。";
  private volatile Serial serial;
  private volatile boolean busy, closing;
  private Thread reader;
  private final Frame parent;

  private int fromSecond=-30, toSecond=0;

  public Monitor(PApplet app) {
    this.app=app;
    Component canvas=(Component)app.getSurface().getNative();
    Window win=SwingUtilities.getWindowAncestor(canvas);
    parent=win instanceof Frame?(Frame)win:null;
  }

  public void paint(Graphics2D g) {
    PanelArt art=activePanel;
    synchronized(rawPanel){
      Telemetry.View view=data.snapshot(fromSecond,toSecond);
      Calibration model=calibration;
      if(art.calibrated) Calibration.apply(view,model);
      art.paint(g,view,port,serial!=null,data.recording,data.pending!=null,busy,
        data.written,data.invalid,data.error.isEmpty()?message:data.error,model==null?"係数CSV未選択":model.filename);
    }
  }

  public void click(int x,int y) {
    EventQueue.invokeLater(()->{
      if(busy || closing) return;
      if(PanelArt.RAW_TAB.contains(x,y)){activePanel=rawPanel;return;}
      if(PanelArt.CAL_TAB.contains(x,y)){activePanel=calibratedPanel;return;}
      PanelArt art=activePanel;
      if(art.calibrated && PanelArt.LOAD.contains(x,y)){
        chooseCalibration();
        return;
      }
      for(int i=0;i<art.buttons.length;i++) if(art.buttons[i].contains(x,y)) {
        try { action(i); }
        catch(Exception ex){report(ex);}
        return;
      }
    });
  }

  private void action(int i) throws IOException {
    if(i>=5){ editRange(i-5); return; }
    switch(i){
      case 0:
        if(serial!=null)return;
        String[] ports=Serial.list();
        if(ports.length==0){message="COMポートが見つかりません。USB接続を確認してください。";return;}
        Object choice=JOptionPane.showInputDialog(parent,"RP2040のCOMポート","COMポート選択",
          JOptionPane.PLAIN_MESSAGE,null,ports,Arrays.asList(ports).contains(port)?port:ports[0]);
        if(choice!=null){port=choice.toString();message="「シリアルを開く」で接続します。";}
        break;
      case 1:
        if(data.recording)return;
        if(serial!=null){ disconnect();message="シリアルを閉じました。"; }
        else if(!port.isEmpty())open();
        break;
      case 2:
        if(serial==null||data.pending!=null)return;
        data.start();message="記録中";break;
      case 3:
        if(!data.recording)return;
        data.stop();message="記録を停止しました。「ログを保存」で保存先を選べます。";break;
      case 4:
        if(!data.recording && data.pending!=null)chooseSave();
        break;
    }
  }

  private synchronized void open(){
    if(closing)return;
    Serial device=new Serial(app,port,115200);
    data.resetStream();
    serial=device;
    message="接続しました。データを受信すると表示を更新します。";
    reader=new Thread(()->receive(device),"airdata-serial");
    reader.setDaemon(true);
    reader.start();
  }

  private void receive(Serial device){
    byte[] buf=new byte[8192];
    long check=System.nanoTime();
    try{
      while(serial==device){
        int n=device.readBytes(buf);
        if(n>0)data.accept(buf,n);
        else Thread.sleep(2);
        if(System.nanoTime()-check>2000000000L){
          check=System.nanoTime();
          if(!Arrays.asList(Serial.list()).contains(port))
            throw new IOException("COMポートが切断されました。");
        }
      }
    }catch(InterruptedException ex){
      Thread.currentThread().interrupt();
    }catch(Exception ex){
      EventQueue.invokeLater(()->{
        if(serial==device){disconnect();report(ex);}
      });
    }
  }

  private synchronized void disconnect(){
    Serial old=serial;
    serial=null;
    if(reader!=null){
      reader.interrupt();
      try{reader.join();}catch(InterruptedException ex){Thread.currentThread().interrupt();}
      reader=null;
    }
    data.stop();
    if(old!=null)old.stop();
  }

  private void editRange(int k){
    PanelArt art=activePanel;
    JTextField lo=new JTextField(Float.toString(art.low[k]),10), hi=new JTextField(Float.toString(art.high[k]),10);
    JTextField from=new JTextField(Integer.toString(fromSecond)), to=new JTextField(Integer.toString(toSecond));
    JPanel fields=new JPanel(new GridLayout(4,2,8,8));
    fields.add(new JLabel("最小 ["+art.unit(k)+"]"));fields.add(lo);
    fields.add(new JLabel("最大 ["+art.unit(k)+"]"));fields.add(hi);
    fields.add(new JLabel("共通時間軸・開始 [秒]"));fields.add(from);
    fields.add(new JLabel("共通時間軸・終了 [秒]（最新 = 0）"));fields.add(to);
    while(JOptionPane.showConfirmDialog(parent,fields,art.title(k)+" の表示範囲",
          JOptionPane.OK_CANCEL_OPTION,JOptionPane.PLAIN_MESSAGE)==JOptionPane.OK_OPTION){
      try{
        float a=Float.parseFloat(lo.getText().trim()),b=Float.parseFloat(hi.getText().trim());
        int start=Integer.parseInt(from.getText().trim()), end=Integer.parseInt(to.getText().trim());
        if(Float.isFinite(a)&&Float.isFinite(b)&&a<b && start>=-Telemetry.HISTORY_SECONDS && start<end && end<=0){
          synchronized(rawPanel){art.low[k]=a;art.high[k]=b;fromSecond=start;toSecond=end;}
          return;
        }
      }catch(NumberFormatException ignored){}
      JOptionPane.showMessageDialog(parent,"縦軸は最小 < 最大、時間は -600 ≦ 開始 < 終了 ≦ 0 の整数秒で入力してください。");
    }
  }

  private void chooseCalibration(){
    FileDialog dialog=new FileDialog(parent,"較正係数CSVを開く",FileDialog.LOAD);
    dialog.setFile("*.csv");
    dialog.setVisible(true);
    String name=dialog.getFile(), dir=dialog.getDirectory();
    dialog.dispose();
    if(name==null)return;
    try{
      calibration=Calibration.load(Paths.get(dir,name));
      message="較正係数を読み込みました。";
    }catch(IOException ex){
      report(ex);
      JOptionPane.showMessageDialog(parent,ex.getMessage(),"較正係数CSV読込",JOptionPane.ERROR_MESSAGE);
    }
  }

  private void chooseSave(){
    FileDialog dialog=new FileDialog(parent,"CSVログの保存",FileDialog.SAVE);
    String stamp=LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
    dialog.setFile("airdata_"+stamp+".csv");
    dialog.setVisible(true);
    String name=dialog.getFile(), dir=dialog.getDirectory();
    dialog.dispose();
    if(name==null)return;
    if(!name.toLowerCase(Locale.ROOT).endsWith(".csv"))name+=".csv";
    Path target=Paths.get(dir,name);
    if(Files.exists(target) && JOptionPane.showConfirmDialog(parent,target+" を置き換えますか？",
        "上書き確認",JOptionPane.YES_NO_OPTION)!=JOptionPane.YES_OPTION)return;
    busy=true;
    new Thread(()->{
      try{data.save(target);message="保存しました: "+target.getFileName();}
      catch(Exception ex){report(ex);}
      finally{busy=false;}
    },"airdata-csv-save").start();
  }

  private void report(Exception ex){message="エラー: "+ex.getMessage();System.err.println(message);}
  public synchronized void shutdown(){
    if(closing)return;
    closing=true;
    disconnect();
    if(data.pending!=null)System.err.println("未保存CSV: "+data.pending);
  }
}
