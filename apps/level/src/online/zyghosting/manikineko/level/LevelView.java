package online.zyghosting.manikineko.level;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.util.AttributeSet;
import android.view.View;

/** Bubble level: a ring with a bubble that moves with the tilt. tx, ty in [-1, 1]. */
public class LevelView extends View {
    private float tx, ty;
    private boolean flat;
    private final Paint ring = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint bubble = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint cross = new Paint(Paint.ANTI_ALIAS_FLAG);

    public LevelView(Context c, AttributeSet a) {
        super(c, a);
        ring.setStyle(Paint.Style.STROKE);
        ring.setStrokeWidth(6);
        cross.setStyle(Paint.Style.STROKE);
        cross.setStrokeWidth(2);
        cross.setColor(0xFF1B2430);
    }

    void setTilt(float x, float y, boolean isFlat) {
        tx = x;
        ty = y;
        flat = isFlat;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas c) {
        float cx = getWidth() / 2f, cy = getHeight() / 2f, r = Math.min(cx, cy) * 0.85f;
        c.drawLine(cx - r, cy, cx + r, cy, cross);
        c.drawLine(cx, cy - r, cx, cy + r, cross);
        ring.setColor(flat ? 0xFF4FA3E3 : 0xFF7C8A9A);
        c.drawCircle(cx, cy, r, ring);
        c.drawCircle(cx, cy, r * 0.12f, ring);
        bubble.setColor(flat ? 0xFF4FA3E3 : 0xFFE8EEF5);
        float bx = cx + Math.max(-1, Math.min(1, tx)) * (r - 40);
        float by = cy + Math.max(-1, Math.min(1, ty)) * (r - 40);
        c.drawCircle(bx, by, r * 0.1f, bubble);
    }
}
