#FOR CODESPACE USE 
#!/bin/bash

# Function to create and switch to a new branch
# Function to create and switch to a new branch
create_new_branch() {
    read -p "Enter the name of the new branch: " branch_name
    git checkout -b "$branch_name"
    git push -u origin "$branch_name"
    chmod +x edit.sh
    echo "Successfully created and pushed the branch: $branch_name"
    echo "Made edit.sh executable."
}

# Function to push the current branch to GitHub
# Function to push the current branch with commit details
push_branch() {
    read -p "Do you want to push your changes? (y/n): " action

    if [[ "$action" == "y" || "$action" == "yes" ]]; then
        read -p "Which file(s) do you want to commit? (comma-separated, e.g., data.py,script.py): " files_input
        IFS=',' read -ra files <<< "$files_input"  # Splitting the input by commas into an array

        echo "Adding files..."
        for file in "${files[@]}"; do
            git add "$file"  # Add the file to the staging area
            echo "Added: $file"
        done

        read -p "What is your commit message?: " commit_msg  # Prompt for a commit message
        echo "Committing..."
        git commit -m "$commit_msg"  # Commit the changes with the provided message

        echo "Pushing..."
        git push  # Push the commit to the remote repository
        echo "Push complete."

    else
        echo "No push action performed."
    fi
}


# Function to list branches and allow user to select one to switch to
# Function to switch to a remote feature branch or main
# Function to switch to any remote branch under origin/ except HEAD
switch_branch() {
    git fetch --all  # Fetch all remote branches

    # List all remote origin branches except HEAD, and strip 'origin/' prefix
    branches=$(git branch -r | grep 'origin/' | grep -v 'HEAD' | sed 's|origin/||' | sort -u)

    if [ -z "$branches" ]; then
        echo "No remote branches found."
        return
    fi

    echo "Available remote branches to switch to:"
    PS3="Select a branch to switch to: "
    select branch in $branches; do
        if [ -n "$branch" ]; then
            # If already exists locally
            if git show-ref --verify --quiet "refs/heads/$branch"; then
                git checkout "$branch"
            else
                git checkout --track origin/"$branch"
            fi
            echo "Switched to branch: $branch"

            # Check if 'edit.sh' exists in the 'main' branch
            git checkout main -- edit.sh 2>/dev/null

            # Check if the file was copied from main branch, if it exists
            if [ -f "edit.sh" ]; then
                echo "Creating a new 'edit.sh' in branch $branch"
                cp edit.sh "edit.sh"  # Copy the 'edit.sh' content into the branch
                chmod +x "edit.sh"  # Make it executable
                echo "Successfully created and made 'edit.sh' executable in $branch."
            else
                echo "No 'edit.sh' found in the 'main' branch to copy."
            fi

            break
        else
            echo "Invalid selection, please try again."
        fi
    done
}


# Function to pull the latest changes
pull_changes() {
    git fetch
    git pull
    echo "Successfully pulled the latest changes."
}

# Function to check repository status
check_status() {
    git status
}

# Function to delete a branch
# Function to delete a branch
# Function to delete a branch
# Function to delete a branch from local, remote, and prune stale refs
delete_branch() {
    git fetch --all  # Make sure all remotes are up to date

    # Get remote branches, excluding HEAD, clean format
    branches=$(git branch -r | grep -v 'HEAD' | grep 'origin/' | sed 's|origin/||' | sort -u)

    echo "Available remote branches to delete:"
    PS3="Select a branch to delete: "
    select branch in $branches; do
        if [ -n "$branch" ]; then
            read -p "Are you sure you want to delete '$branch' from all remotes and locally? (y/n): " confirm
            if [[ $confirm != [yY] ]]; then
                echo "Cancelled branch deletion."
                break
            fi

            # Delete from all remotes
            for remote in $(git remote); do
                echo "Deleting $branch from remote: $remote"
                git push "$remote" --delete "$branch" 2>/dev/null
            done

            # Delete local branch (if it exists)
            if git show-ref --verify --quiet "refs/heads/$branch"; then
                git branch -D "$branch"
                echo "Deleted local branch: $branch"
            fi

            # Prune all stale remote references
            git remote prune origin >/dev/null
            for remote in $(git remote); do
                git remote prune "$remote" >/dev/null
            done

            echo "Deleted all references to: $branch"
            break
        else
            echo "Invalid selection, please try again."
        fi
    done
}
# Function to merge one branch into another
merge_branch() {
    git fetch --all  # Ensure all branches are fetched

    # Get relevant remote branches
    branches=$(git branch -r | grep 'origin/' | grep -v 'HEAD' | sed 's|origin/||' | sort -u)

    if [ -z "$branches" ]; then
        echo "No available remote branches to merge."
        return
    fi

    echo "Available remote branches:"
    PS3="Select the branch you want to merge FROM: "
    select merge_from in $branches; do
        if [ -n "$merge_from" ]; then
            break
        else
            echo "Invalid selection."
        fi
    done

    PS3="Select the branch you want to merge INTO: "
    select merge_into in $branches; do
        if [ -n "$merge_into" ]; then
            break
        else
            echo "Invalid selection."
        fi
    done

    if [ "$merge_from" == "$merge_into" ]; then
        echo "Error: Cannot merge a branch into itself."
        return
    fi

    # Switch to target branch and update it
    if git show-ref --verify --quiet "refs/heads/$merge_into"; then
        git checkout "$merge_into"
    else
        git checkout --track origin/"$merge_into"
    fi
    git pull origin "$merge_into"

    # Merge source into target
    echo "Merging 'origin/$merge_from' into '$merge_into'..."
    if ! git merge --no-edit origin/"$merge_from"; then
        echo "Merge conflict occurred or manual merge commit is needed."
        echo "Please resolve conflicts and run 'git commit' manually."
        return 1
    fi

    # Push the merged changes
    git push origin "$merge_into"

    echo "Successfully merged '$merge_from' into '$merge_into' and pushed to GitHub."
}


view_log() {
    git log --oneline --decorate --graph --abbrev-commit
}

# Main menu
echo "What would you like to do?"
echo "1. Create a new branch"
echo "2. Push the current branch"
echo "3. Switch to another branch"
echo "4. Pull the latest changes"
echo "5. Check the repository status"
echo "6. Delete a branch"
echo "7. View commit history"
echo "8. Merge branch"
read -p "Enter your choice (1-8): " choice

case $choice in
    1) create_new_branch ;;
    2) push_branch ;;
    3) switch_branch ;;
    4) pull_changes ;;
    5) check_status ;;
    6) delete_branch ;;
    7) view_log ;;
    8) merge_branch ;;
    *) echo "Invalid option. Please select a number from the list." ;;
esac