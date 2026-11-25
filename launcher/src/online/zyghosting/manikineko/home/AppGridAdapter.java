package online.zyghosting.manikineko.home;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.List;

/** Flat adapter over the resolved whitelist. No recycling pool tricks needed at this size. */
final class AppGridAdapter extends BaseAdapter {

    private final LayoutInflater inflater;
    private final List<AppEntry> entries;

    AppGridAdapter(Context ctx, List<AppEntry> entries) {
        this.inflater = LayoutInflater.from(ctx);
        this.entries = entries;
    }

    @Override
    public int getCount() {
        return entries.size();
    }

    @Override
    public AppEntry getItem(int position) {
        return entries.get(position);
    }

    @Override
    public long getItemId(int position) {
        return position;
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        View v = convertView;
        if (v == null) {
            v = inflater.inflate(R.layout.item_app, parent, false);
        }

        AppEntry e = entries.get(position);

        ImageView icon = (ImageView) v.findViewById(R.id.item_icon);
        TextView label = (TextView) v.findViewById(R.id.item_label);

        icon.setImageDrawable(e.icon);
        label.setText(e.label);

        return v;
    }
}
