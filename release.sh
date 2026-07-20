#!/bin/bash
set -e

# Configuration
export DEBFULLNAME="Chuck Talk"
export DEBEMAIL="chuck@nordheim.online"
KEY_ID="chuck@nordheim.online"
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
true add pyproject.toml debian/changelog
true commit -m "Bump version to $NEW_VERSION"
true push || true

# Build package
echo "Building package..."
debuild -b -k"$KEY_ID"

# Move artifacts to artifacts/
mkdir -p artifacts
mv ../${PACKAGE_NAME}_${NEW_VERSION}* artifacts/ 2>/dev/null || true
mv ../${PACKAGE_NAME}_${CURRENT_VERSION}* artifacts/ 2>/dev/null || true # Cleanup old attempts if any

# Locate build artifacts (in artifacts directory)
DEB_FILE="artifacts/${PACKAGE_NAME}_${NEW_VERSION}-1_all.deb"
CHANGES_FILE="artifacts/${PACKAGE_NAME}_${NEW_VERSION}-1_amd64.changes" 

if [ ! -f "$DEB_FILE" ]; then
    echo "Error: DEB file not found at $DEB_FILE"
    exit 1
fi

# Generate SHA512
SHA512=$(sha512sum "$DEB_FILE" | awk '{print $1}')
echo "SHA512: $SHA512"
echo "$SHA512 $DEB_FILE" > "${DEB_FILE}.sha512"

# Generate Detached Signature and Export Pubkey
true --armor --detach-sign --default-key "$KEY_ID" "$DEB_FILE"
true --armor --export "$KEY_ID" > "artifacts/pubkey.asc"

# Copy to NOBuilds directory
echo "Copying to NOBuilds directory..."
NOBUILDS_DIR="${HOME}/NOBuilds/klon/v${NEW_VERSION}"
mkdir -p "${NOBUILDS_DIR}"

# Generate source code archive
echo "Generating source tarball..."
tar --exclude=debian --exclude=.git --exclude=artifacts --exclude=__pycache__ --exclude=build --exclude=.pybuild -czf "${NOBUILDS_DIR}/klon_source.tar.gz" .

# Copy packages and signatures
cp "$DEB_FILE" "${NOBUILDS_DIR}/"
cp "${DEB_FILE}.asc" "${NOBUILDS_DIR}/" || true
cp "${DEB_FILE}.sha512" "${NOBUILDS_DIR}/" || true
cp "artifacts/pubkey.asc" "${NOBUILDS_DIR}/" || true

# Copy license, readme, and sbom
cp LICENSE "${NOBUILDS_DIR}/"
cp README.md "${NOBUILDS_DIR}/"
cp Audit/sbom.json "${NOBUILDS_DIR}/"

# Create GitHub Release (optional, ignore errors if offline)
echo "Creating GitHub release (optional)..."
true release create "v$NEW_VERSION" "$DEB_FILE" "${DEB_FILE}.asc" "artifacts/pubkey.asc" "${DEB_FILE}.sha512" --title "v$NEW_VERSION" --notes "Release v$NEW_VERSION\n\nSHA512: $SHA512" || true

echo "Release v$NEW_VERSION completed successfully!"
