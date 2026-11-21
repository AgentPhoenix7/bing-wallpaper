package net.ameizi.wallpaper;

import java.io.Serializable;

public record Image(String date, String desc, String url) implements Serializable {

    private static final String LARGE_URL_FORMAT = "%s&w=960";

    @Override
    public String toString() {
        String fullUrl = this.url + "&pid=hp&w=384&h=216&rs=1&c=4";
        return String.format("![%s](%s) %s [download 4k](%s)", this.desc, fullUrl, this.date, this.url);
    }

    public String largeUrl() {
        return String.format(LARGE_URL_FORMAT, this.url);
    }

    public String markdown() {
        return String.format("%s | [%s](%s)", this.date, this.desc, this.url) + System.lineSeparator() + System.lineSeparator();
    }

    public String getDate() {
        return date;
    }

    public String getDesc() {
        return desc;
    }

    public String getUrl() {
        return url;
    }
}
