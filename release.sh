#!/bin/bash
set -e

# Configuration
KEY_ID="Chuck Talk <cwtalk1@gmail.com>"
PACKAGE_NAME="klon"

# check for required commands
command -v dch >/dev/null 2>&1 || { echo >&2 "dch (devscripts) is required but not installed. Aborting."; exit 1; }
command -v gh >/dev/null 2>&1 || { echo >&2 "gh cli is required but not installed. Aborting."; exit 1; }

# Get current version from changelog
CURRENT_VERSION=$(dpkg-parsechangelog --show-field Version | cut -d- -f1)
echo "Current version: $CURRENT_VERSION"

# Increment patch version
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
PATCH_VERSION=${VERSION_PARTS[2]}
NEW_PATCH_VERSION=$((PATCH_VERSION + 1))
NEW_VERSION="${VERSION_PARTS[0]}.${VERSION_PARTS[1]}.$NEW_PATCH_VERSION"
echo "New version: $NEW_VERSION"

# Update pyproject.toml
sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
echo "Updated pyproject.toml to $NEW_VERSION"

# Update changelog
dch -v "$NEW_VERSION-1" "New release $NEW_VERSION"
dch -r ""

# Commit version bump
git add pyproject.toml debian/changelog
git commit -m "Bump version to $NEW_VERSION"
git push

# Build package
echo "Building package..."
debuild -k"$KEY_ID"

# Locate build artifacts (parent directory)
DEB_FILE="../${PACKAGE_NAME}_${NEW_VERSION}-1_all.deb"
CHANGES_FILE="../${PACKAGE_NAME}_${NEW_VERSION}-1_amd64.changes" 

if [ ! -f "$DEB_FILE" ]; then
    echo "Error: DEB file not found at $DEB_FILE"
    exit 1
fi

# Generate SHA512
SHA512=$(sha512sum "$DEB_FILE" | awk '{print $1}')
echo "SHA512: $SHA512"
echo "$SHA512 $DEB_FILE" > "${DEB_FILE}.sha512"

# Create GitHub Release
echo "Creating GitHub release..."
gh release create "v$NEW_VERSION" "$DEB_FILE" --title "v$NEW_VERSION" --notes "Release v$NEW_VERSION\n\nSHA512: $SHA512"

echo "Release v$NEW_VERSION completed successfully!"
