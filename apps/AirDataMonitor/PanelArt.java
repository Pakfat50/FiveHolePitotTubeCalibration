import java.awt.*;
import java.awt.geom.*;
import java.util.Locale;

/** 画面座標は1200×740を基準にする。数値は等幅・右揃え・固定小数点で描く。 */
public class PanelArt {
  public static final int W=1200,H=740;
  private static final Color INK=new Color(27,46,63), MUTED=new Color(76,98,113),
    GRID=new Color(214,224,230), BG=new Color(241,245,247);
  private static final Color[] COLORS={new Color(0,119,106),new Color(31,92,163),new Color(176,82,27)};
  public static final String[] NAMES={"Total","AoA","AoS"};
  public final float[] low={0,-20,-20}, high={150,20,20};
  public final Rectangle[] buttons=new Rectangle[8];
  public static final Rectangle RAW_TAB=new Rectangle(288,9,108,34);
  public static final Rectangle CAL_TAB=new Rectangle(401,9,118,34);
  public static final Rectangle LOAD=new Rectangle(535,9,142,34);
  public final boolean calibrated;
  private final String[] plots;
  public String unit(int k){ return calibrated && k!=0?"°":"Pa"; }
  public String title(int k){ return plots[k]; }
  private static final String UI=chooseFont();

  private static String chooseFont() {
    for(String s:new String[]{"Yu Gothic UI","Meiryo","Noto Sans CJK JP","Dialog"})
      if(new Font(s,0,12).canDisplay('録')) return s;
    return "Dialog";
  }
  public PanelArt(boolean calibrated){
    this.calibrated=calibrated;
    plots=calibrated ? new String[]{"推定動圧 q_ref","迎角 α","横滑り角 β"} :
                       new String[]{"Total Δp","AoA Δp","AoS Δp"};
    int[] x={18,172,333,451,569}, w={146,153,110,110,133};
    for(int i=0;i<5;i++) buttons[i]=new Rectangle(x[i],70,w[i],36);
    for(int i=0;i<3;i++) buttons[i+5]=new Rectangle(29,241+181*i,105,27);
  }
  private void label(Graphics2D g,String s,int x,int y,int size,Color c,boolean bold){
    g.setFont(new Font(UI,bold?Font.BOLD:Font.PLAIN,size));g.setColor(c);g.drawString(s,x,y);
  }
  private void num(Graphics2D g,String s,int right,int y,int size,Color c){
    g.setFont(new Font(Font.MONOSPACED,Font.BOLD,size));g.setColor(c);
    g.drawString(s,right-g.getFontMetrics().stringWidth(s),y);
  }
  private String fmt(float v,int digits,boolean sign){
    if(!Float.isFinite(v)) return "—";
    return String.format(Locale.ROOT,"%"+(sign?"+":"")+"."+digits+"f",v);
  }
  private void card(Graphics2D g,int x,int y,int w,int h){
    g.setColor(Color.WHITE);g.fillRoundRect(x,y,w,h,12,12);
    g.setColor(GRID);g.drawRoundRect(x,y,w,h,12,12);
  }
  private void button(Graphics2D g,Rectangle r,String s,boolean on,boolean accent){
    g.setColor(!on?BG:accent?COLORS[0]:Color.WHITE);g.fillRoundRect(r.x,r.y,r.width,r.height,8,8);
    g.setColor(GRID);g.drawRoundRect(r.x,r.y,r.width,r.height,8,8);
    label(g,s,r.x+10,r.y+r.height/2+5,r.height<30?13:15,!on?new Color(139,151,159):accent?Color.WHITE:INK,true);
  }
  public void paint(Graphics2D g,Telemetry.View v,String port,boolean connected,boolean rec,
                    boolean pending,boolean busy,long rows,long invalid,String status,String coefficientFile){
    g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
    g.setColor(BG);g.fillRect(0,0,W,H);g.setColor(INK);g.fillRect(0,0,W,53);
    label(g,"エアデータモニター",20,35,24,Color.WHITE,true);
    button(g,RAW_TAB,"生データ",true,!calibrated);
    button(g,CAL_TAB,"較正データ",true,calibrated);
    if(calibrated){
      button(g,LOAD,"較正係数CSV読込",!busy,false);
      Graphics2D clipped=(Graphics2D)g.create();
      clipped.clipRect(687,0,310,53);
      label(clipped,coefficientFile,687,33,16,Color.WHITE,true);
      clipped.dispose();
    }
    num(g,(v.tick<0?"—":Long.toString(v.tick))+" ms",W-22,34,18,Color.WHITE);
    String[] titles={port.isEmpty()?"COMポート":port,connected?"シリアルを閉じる":"シリアルを開く","記録開始","記録停止","ログを保存"};
    boolean[] active={!connected,!rec && (connected||!port.isEmpty()),connected&&!pending,rec,pending&&!rec};
    for(int i=0;i<5;i++)button(g,buttons[i],titles[i],active[i]&&!busy,i==2);
    // ポート選択の矢印は、Windowsのフォントに依存しない三角形として描く。
    Rectangle selector=buttons[0];
    int arrowX=selector.x+selector.width-17, arrowY=selector.y+selector.height/2;
    g.setColor(active[0]&&!busy?INK:new Color(139,151,159));
    g.fillPolygon(new int[]{arrowX-5,arrowX+5,arrowX},new int[]{arrowY-2,arrowY-2,arrowY+4},3);
    label(g,connected?"● 接続中":"○ 未接続",736,94,16,connected?COLORS[0]:MUTED,true);
    label(g,rec?"● 記録中":pending?"未保存":"記録待機",846,94,16,rec?COLORS[2]:MUTED,true);
    num(g,rows+" rows",1180,94,17,INK);
    for(int k=0;k<3;k++)plot(g,v,k);
    gauge(g,779,122,0,v.current[7]);gauge(g,988,122,1,v.current[8]);
    card(g,779,367,405,319);
    label(g,"センサー値",796,397,18,INK,true);
    row(g,430,"加速度 [m/s²]",new String[]{"X","Y","Z"},v.current,9,2,true);
    row(g,482,"角速度 [rad/s]",new String[]{"X","Y","Z"},v.current,12,2,true);
    row(g,534,"差圧計温度 [°C]",NAMES,v.current,3,1,false);
    label(g,"BMP280 温度 [°C]",796,620,16,MUTED,false);num(g,fmt(v.current[15],1,false),1162,620,23,INK);
    label(g,"BMP280 気圧 [hPa]",796,666,16,MUTED,false);num(g,fmt(v.current[16],1,false),1162,666,23,INK);
    label(g,status,18,724,14,MUTED,false);num(g,"形式不正 "+invalid,1180,724,14,MUTED);
  }
  private void row(Graphics2D g,int y,String title,String[] names,float[] data,int off,int digits,boolean sign){
    label(g,title,796,y,14,MUTED,false);
    for(int i=0;i<3;i++){
      label(g,names[i],798+i*126,y+22,13,MUTED,true);
      num(g,fmt(data[off+i],digits,sign),911+i*126,y+23,19,INK);
    }
  }
  private void plot(Graphics2D g,Telemetry.View v,int k){
    int y=122+181*k, left=215,right=745,top=y+16,bottom=y+142;
    card(g,16,y,747,175);label(g,title(k),29,y+37,calibrated?19:23,INK,true);
    num(g,fmt(v.current[k],1,k!=0),147,y+82,29,COLORS[k]);
    label(g,unit(k),31,y+104,15,MUTED,false);button(g,buttons[5+k],"範囲設定…",true,false);
    double lo=low[k], span=(double)high[k]-lo;
    for(int i=0;i<=2;i++){
      int gy=bottom-(bottom-top)*i/2;
      g.setColor(GRID);g.drawLine(left,gy,right,gy);
      double val=lo+span*i/2;
      String tick=java.math.BigDecimal.valueOf(val).stripTrailingZeros().toPlainString();
      if(tick.length()>7)tick=String.format(Locale.ROOT,"%.1e",val);
      num(g,tick,left-6,gy+5,12,MUTED);
    }
    for(int i=0;i<=6;i++){
      int gx=left+(right-left)*i/6;
      g.setColor(GRID);g.drawLine(gx,top,gx,bottom);
      if(k==2){
        double second=v.fromSecond+(v.toSecond-v.fromSecond)*i/6.0;
        String tick=second==Math.rint(second)?Integer.toString((int)second):String.format(Locale.ROOT,"%.2f",second);
        num(g,tick+(i==6?" s":""),gx+6,bottom+21,12,MUTED);
      }
    }
    Graphics2D p=(Graphics2D)g.create();p.clipRect(left,top,right-left+1,bottom-top+1);
    p.setColor(COLORS[k]);p.setStroke(new BasicStroke(1.7f));
    Path2D path=new Path2D.Float();boolean prev=false;
    for(int i=0;i<v.ageMs.length;i++){
      float dp=v.dp[k][i];if(!Float.isFinite(dp)){prev=false;continue;}
      double x=left+(v.ageMs[i]-v.fromSecond*1000L)*(right-left)/((v.toSecond-v.fromSecond)*1000.0);
      double py=bottom-(dp-lo)/span*(bottom-top);
      // 極端な範囲外の座標でもJava2Dの描画範囲を超えないようにする。
      py=Math.max(-1e7,Math.min(1e7,py));
      if(prev && v.ageMs[i]-v.ageMs[i-1]<=50)path.lineTo(x,py);else path.moveTo(x,py);
      prev=true;
    }
    p.draw(path);p.dispose();
  }
  private void gauge(Graphics2D g,int x,int y,int k,float value){
    card(g,x,y,196,232);
    label(g,k==0?"ピッチ / Pitch":"ロール / Roll",x+13,y+30,17,INK,true);
    int cx=x+98,cy=y+127,r=66;
    double sweep=k==0?90:150,max=k==0?90:180;
    g.setColor(GRID);g.setStroke(new BasicStroke(3));
    g.draw(new Arc2D.Double(cx-r,cy-r,2*r,2*r,90-sweep,2*sweep,Arc2D.OPEN));
    for(int i=-6;i<=6;i++){
      double a=Math.toRadians(i*sweep/6);int inner=i%3==0?r-11:r-6;
      g.setColor(INK);g.draw(new Line2D.Double(cx+inner*Math.sin(a),cy-inner*Math.cos(a),cx+r*Math.sin(a),cy-r*Math.cos(a)));
    }
    g.setStroke(new BasicStroke(1));
    num(g,"0",cx+4,cy-r-6,12,MUTED);
    int ty=k==0?cy+18:cy+71;
    num(g,k==0?"−90":"−180",cx-(k==0?48:23),ty,12,MUTED);
    num(g,k==0?"+90":"+180",cx+(k==0?82:56),ty,12,MUTED);
    if(Float.isFinite(value)){
      double a=Math.toRadians(Math.max(-max,Math.min(max,value))*sweep/max);
      g.setColor(COLORS[k]);g.setStroke(new BasicStroke(4,BasicStroke.CAP_ROUND,BasicStroke.JOIN_ROUND));
      g.draw(new Line2D.Double(cx,cy,cx+(r-12)*Math.sin(a),cy-(r-12)*Math.cos(a)));
      g.fillOval(cx-5,cy-5,10,10);g.setStroke(new BasicStroke(1));
    }
    num(g,fmt(value,1,true)+"°",x+159,y+221,27,COLORS[k]);
  }
}
