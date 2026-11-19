// Processing 4 / Java モード。追加GUIライブラリは使用しない。
import processing.serial.*;
import processing.awt.PGraphicsJava2D;
import java.awt.Graphics2D;
import java.awt.GraphicsEnvironment;
import java.awt.Rectangle;

Monitor monitor;

void settings() {
  size(1200, 740, JAVA2D);
}

void setup() {
  surface.setTitle("エアデータモニター");
  surface.setResizable(true);
  Rectangle area = GraphicsEnvironment.getLocalGraphicsEnvironment().getMaximumWindowBounds();
  float scale = min(1.0f, min((area.width-24)/1200.0f, (area.height-48)/740.0f));
  if (scale < 1.0f) surface.setSize(int(1200*scale), int(740*scale));
  monitor = new Monitor(this);
  frameRate(10);
}

void draw() {
  Graphics2D ctx = (Graphics2D)((PGraphicsJava2D)g).g2.create();
  try {
    ctx.scale(width/1200.0f, height/740.0f);
    monitor.paint(ctx);
  } finally {
    ctx.dispose();
  }
}

void mousePressed() {
  monitor.click(mouseX*1200/width, mouseY*740/height);
}

public void dispose() {
  if (monitor != null) monitor.shutdown();
  super.dispose();
}
