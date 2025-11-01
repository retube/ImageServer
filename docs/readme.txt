
On Raspberry Pi:

- Run X11 window manager (not Wayland/Wayfire)
- Enable Screen Blanking (Preferences -> Raspberry Pi Configuration -> Display -> Screen Banking On)
    - This ensures DPMS is running

- Create file: /etc/systemd/system/pir-display.service with the following content

    [TBC]


 - Add to startup:

    sudo systemctl daemon-reload
    sudo systemctl enable --now pir-display.service




