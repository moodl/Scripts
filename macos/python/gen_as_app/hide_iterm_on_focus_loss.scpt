on idle
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        if frontApp is not "iTerm2" then
            tell application "iTerm2" to set miniaturized of windows to true
        end if
    end tell
    return 5 -- Check every 5 seconds
end idle