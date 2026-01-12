# 📂 File Organizer

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
[Google Cloud](https://img.shields.io/badge/Google_Cloud-34a853?style=for-the-badge&logo=google-cloud&logoColor=white)
[![Mistral AI](https://img.shields.io/badge/Mistral%20AI-FA520F?style=for-the-badge&logo=mistral-ai&logoColor=white)](#)

File Organizer is a Python application designed to monitor a specified directory for newly created files and automatically categorize them into predefined folders based on their file types. It utilizes Google Cloud APIs for image, video, audio, and document analysis, as well as Mistral AI for generating intelligent subfolder names. This tool helps streamline file management by organizing files into categories such as Images, Videos, Audio, Documents, Archives, and Code.

---

## ✨ Features

- **🤖 Automatic File Categorization**: Files are organized into categories based on their extensions.
- **🖼️ Content Analysis**: Uses Google Cloud Vision for image analysis, Google Cloud Video Intelligence for video analysis, Google Cloud Speech-to-Text for audio transcription, and PDFPlumber for document text extraction.
- **🧠 Intelligent Subfolder Naming**: Mistral AI suggests subfolder names based on the content of the files and existing folder names.
- **📜 Logging**: The application logs all operations and errors for easy debugging and tracking.
- **📝 Metadata Generation**: Metadata for each file is generated and saved alongside the file in JSON format.

  ---

## ✅ Requirements
=======
- Python 3.7 or higher
- Google Cloud SDK with the necessary APIs enabled (Vision, Video Intelligence, Speech)
- Mistral AI API key
- Required Python libraries listed in `requirements.txt` (see below)

---

## 🚀 Installation
=======

1. Clone this repository:

   ```bash
   git clone https://github.com/yourusername/file-organizer.git
   cd file-organizer
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up Google Cloud credentials:

   - Create a service account in Google Cloud and download the JSON credentials file.
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the credentials file:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/credentials.json"
   ```

4. Obtain your Mistral API key and replace the placeholder in the code.

---

## ▶️ Usage
=======

1. Create an `inbox` directory in the project root. This is where you will drop files for organization.

2. Create a `destination` directory in the project root. This is where organized files will be moved.

3. Run the application:

   ```bash
   python backend/monitor.py
   ```

4. Drop files into the `inbox` directory. The application will automatically organize them into the `destination` directory based on their type.

---

## 📋 Logging

The application logs its activities to `file_organization.log`, which includes information about processed files, errors, and metadata generation.

---

## 🤝 Contributing

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- Google Cloud for providing powerful API services.
- Mistral AI for intelligent content analysis.
