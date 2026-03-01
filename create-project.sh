#!/bin/bash

# ─── Resolve the armada root (where this script lives) ───
ARMADA_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_TEMPLATE="$ARMADA_DIR/services/project"
FIRST_TRY_TEMPLATE="$ARMADA_DIR/first-try/first-try-project"
AGENT_PATH="$ARMADA_DIR/services/agent"

# ─── Check dependencies ───
if ! command -v zenity &>/dev/null; then
    echo "Error: 'zenity' is required for the folder selection dialog."
    echo "Install it with: sudo apt install zenity"
    exit 1
fi

# ─── Choose mode ───
MODE=$(zenity --list \
    --title="Armada" \
    --text="What do you want to create?" \
    --column="Option" --column="Description" \
    "1" "New Project" \
    "2" "First-try Project - Discover Armada" \
    --width=450 --height=250)

if [ -z "$MODE" ]; then
    echo "Cancelled."
    exit 0
fi

if [ "$MODE" = "1" ]; then
    # ─── New Project ───

    if [ ! -d "$PROJECT_TEMPLATE" ]; then
        echo "Error: Template directory not found at $PROJECT_TEMPLATE"
        exit 1
    fi

    # ─── Ask for project name ───
    PROJECT_NAME=$(zenity --entry \
        --title="New Armada Project" \
        --text="Enter the project name:" \
        --width=400)

    if [ -z "$PROJECT_NAME" ]; then
        echo "Cancelled: no project name provided."
        exit 0
    fi

    # ─── Ask for destination folder ───
    DEST_DIR=$(zenity --file-selection \
        --directory \
        --title="Select where to create the project" \
        --filename="$HOME/")

    if [ -z "$DEST_DIR" ]; then
        echo "Cancelled: no destination selected."
        exit 0
    fi

    # ─── Create the project ───
    TARGET="$DEST_DIR/$PROJECT_NAME"

    if [ -d "$TARGET" ]; then
        zenity --error --text="A folder named '$PROJECT_NAME' already exists at:\n$DEST_DIR" --width=400
        exit 1
    fi

    cp -r "$PROJECT_TEMPLATE" "$TARGET"

    # ─── Update workbench/agent_path ───
    echo -n "$AGENT_PATH" > "$TARGET/workbench/agent_path"

    # ─── Open the new project folder ───
    xdg-open "$TARGET" 2>/dev/null &

    zenity --info \
        --title="Project Created" \
        --text="Project '$PROJECT_NAME' successfully created at:\n$TARGET" \
        --width=400

    echo "Project '$PROJECT_NAME' created at $TARGET"

elif [ "$MODE" = "2" ]; then
    # ─── First-try Project ───

    if [ ! -d "$FIRST_TRY_TEMPLATE" ]; then
        echo "Error: First-try template directory not found at $FIRST_TRY_TEMPLATE"
        exit 1
    fi

    # ─── Ask for destination folder ───
    DEST_DIR=$(zenity --file-selection \
        --directory \
        --title="Select where to store the First-try project" \
        --filename="$HOME/")

    if [ -z "$DEST_DIR" ]; then
        echo "Cancelled: no destination selected."
        exit 0
    fi

    # ─── Create the project ───
    TARGET="$DEST_DIR/first-try-project"

    if [ -d "$TARGET" ]; then
        zenity --error --text="A folder named 'first-try-project' already exists at:\n$DEST_DIR" --width=400
        exit 1
    fi

    cp -r "$FIRST_TRY_TEMPLATE" "$TARGET"

    # ─── Update workbench/agent_path ───
    echo -n "$AGENT_PATH" > "$TARGET/workbench/agent_path"

    # ─── Open the new project folder ───
    xdg-open "$TARGET" 2>/dev/null &

    zenity --info \
        --title="First-try Project Created" \
        --text="First-try project successfully created at:\n$TARGET" \
        --width=400

    echo "First-try project created at $TARGET"
fi
