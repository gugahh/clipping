import argostranslate.package
import argostranslate.translate

# One-time download (run once or on first launch)
argostranslate.package.update_package_index()
argostranslate.package.install_from_index("en_pb")  # English -> Portuguese (Brazil)