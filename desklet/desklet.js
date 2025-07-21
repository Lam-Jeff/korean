const Desklet = imports.ui.desklet;
const GLib = imports.gi.GLib;
const St = imports.gi.St;
const Mainloop = imports.mainloop;
const Lang = imports.lang;
const DeskletManager = imports.ui.deskletManager;
const Gtk = imports.gi.Gtk;
const Gio = imports.gi.Gio;
const Clutter = imports.gi.Clutter;

/**
  * Returns a string by replacing keywords in a template with the data to display.
  * @param {String} template A string to use for displaying the data.
  * @param {{keyWordInTemplateToReplace: String, ...}} data The data to display.
  * @returns {String} template The string to display.
  */
function applyTemplate(template, data) {
  template = String(template);
  for (let key in data) {
    let regex = new RegExp(`{{${key}}}`, "g");
    template = template.replace(regex, data[key]);
  }
  return template;
}

/**
  * Returns an array containing the keywords to replace in the string.
  * @param {String} template The string containing keywords.
  * @returns {Array[String]} res An array with keywords.
  */
function searchKeyWord(template) {
  const regex = /{{(.*?)}}/g;
  let res = [];
  let match = regex.exec(template)

  while (match !== null) {
    res.push(match[1]);
    match = regex.exec(template);
  }

  return res;
}

/**
  * Returns an array with environment variables.
  * @param {String} filePath Path to the .env file.
  * @returns {Array[String]} env An array with environment variables.
  */
function loadEnv(filePath) {
  const env = {};

  try {
    const file = Gio.File.new_for_path(filePath);
    const [success, contents] = file.load_contents(null);
    let decoder = new TextDecoder("utf-8");
    let text = decoder.decode(contents);
    const lines = text.split('\n');

    for (let line of lines) {
      line = line.trim();
      if (!line || line.startsWith('#')) continue;

      const [key, ...rest] = line.split('=');
      if (key && rest.length) {
        env[key.trim()] = rest.join('=').trim();
      }
    }
  } catch (e) {
    log(`Erreur lecture .env: ${e.message}`);
  }

  return env;
}

/**
  * Apply a fade in transition on a label element.
  * @param {St.Label} label A label element.
  * @param {String} text A string inside the label.
  * @param {number} duration The duration of the transition.
  */
function fadeInLabel(label, text, duration = 500) {
  if (!label) return;
  label.ease({
    opacity: 0,
    duration: duration,
    mode: Clutter.AnimationMode.EASE_OUT_QUAD,
    onComplete: () => {
      label.set_text(text);
      label.ease({
        opacity: 255,
        duration: duration,
        mode: Clutter.AnimationMode.EASE_IN_QUAD
      });
    }
  });
}

function main(metadata, desklet_id) {

  return new FlashcardDesklet(metadata, desklet_id);
}

function FlashcardDesklet(metadata, desklet_id) {
  this._init(metadata, desklet_id);
}

FlashcardDesklet.prototype = {
  __proto__: Desklet.Desklet.prototype,

  _init: function(metadata, desklet_id) {
    Desklet.Desklet.prototype._init.call(this, metadata, desklet_id);
    this._isFlipped = false;
    this._textRecto = "";
    this._textVerso = "";
    this._data = [];

    this._title = "Title Example...";
    this._progression = 1;
    this._maxProgression = 10; // default. If the query retrieves X rows then change this.
    this._path = String(metadata.path instanceof Gio.File ? metadata.path.get_path() : metadata.path);
    this._loadStylesheet(this._path + "/stylesheet.css");


    this.container = new St.BoxLayout({
      vertical: true,
      style_class: "desklet-container",
      track_hover: true
    });

    this.footerContainer = new St.BoxLayout({
      vertical: false,
      track_hover: true,
      style_class: "footer-container"
    })

    this.titleLabel = new St.Label({
      text: this._title,
      style_class: "flashcard-title"
    });
    this.progressionLabel = new St.Label({
      text: String(this._progression) + "/" + String(this._maxProgression),
      style_class: "flashcard-progression"
    });

    this.flashcardContainer = new St.Bin({ reactive: true, track_hover: true, can_focus: true, x_align: St.Align.MIDDLE, y_align: St.Align.MIDDLE, style_class: "flashcard-container" });
    this.flashcardLabel = new St.Label({ text: "Chargement...", style_class: "flashcard-label" });
    this.flashcardContainer.set_child(this.flashcardLabel);
    this.flashcardContainer.connect('button-press-event', () => {
      this._isFlipped = !this._isFlipped;
      this._updateFlashcardContent();
    });

    this.nextContainer = new St.Bin({ reactive: true, track_hover: true, can_focus: true, x_align: St.Align.MIDDLE, y_align: St.Align.MIDDLE });
    this.nextLabel = new St.Label({ text: "Next flashcard", reactive: true, track_hover: true, can_focus: true, style_class: "next-label" });
    this.nextContainer.set_child(this.nextLabel);
    this.nextContainer.connect('button-press-event', () => {
      this._nextFlashcard();
    });
    this.expander = new St.Widget({ x_expand: true });

    this.footerContainer.add_child(this.nextContainer);
    this.footerContainer.add_child(this.expander);
    this.footerContainer.add_child(this.progressionLabel);

    this.container.add_child(this.titleLabel);
    this.container.add_child(this.flashcardContainer);
    this.container.add_child(this.footerContainer);
    this.setContent(this.container);

    const envPath = GLib.build_filenamev([this._path, ".env"]);
    const env = loadEnv(envPath);

    this.venvPython = env["PATH_TO_PYTHON_ENV"] || "/usr/bin/python3";
    this.scriptPath = env["PATH_TO_SCRIPT"];
    this.queryRes = env["PATH_TO_QUERY_RES"];

    this._update();
  },

  /**
   * Execute python file and initialize the data to display.
   * @returns {boolean} false To prevent infinite loop.
   */
  _update: function() {
    const command = `"${this.venvPython}" "${this.scriptPath}"`;
    GLib.spawn_command_line_async(command);

    Mainloop.timeout_add(1000, Lang.bind(this, this._readJson));

    return false;
  },

  /**
   * Update flashcard's content. Apply a transition.
   */
  _updateFlashcardContent: function() {
    if (this._isFlipped) {
      fadeInLabel(this.flashcardLabel, this._textVerso, 300);
    } else {
      fadeInLabel(this.flashcardLabel, this._textRecto, 300);
    }
  },

  /**
   * Get next flashcard to display.
   */
  _nextFlashcard: function() {
    if (this._progression + 1 <= this._maxProgression) {
      this._progression += 1;
    } else {
      this._progression = 1;
    }
    this._getData(this._data, this._progression - 1);
    this.progressionLabel.set_text(String(this._progression) + "/" + String(this._maxProgression),);
  },

  /**
   * Set text to display.
   * @param {{tags: String, flds: String, sfld: String, qfmt: String, afmt: String}} data A dictionary that contains data to display.
   * @param {number} index The index of the value to display.
   */
  _getData: function(data, index) {
    let flds_splitted = data[index][1].split("\x1f"); // word, translation, example, comment
    let keyWords_afmt = searchKeyWord(data[index][4]);
    let keyWords_qfmt = searchKeyWord(data[index][3]);
    let dictTemp_afmt = {};
    let dictTemp_qmft = {};
    for (const [index, key] of keyWords_afmt.entries()) {
      dictTemp_afmt[key] = flds_splitted[index];
    }
    for (const [index, key] of keyWords_qfmt.entries()) {
      dictTemp_qmft[key] = flds_splitted[index];
    }


    let qfmt = data[index][3].split("|");
    let afmt = data[index][4].split("|");

    this._isFlipped = false;
    this._textRecto = applyTemplate(qfmt, dictTemp_qmft);
    this._textVerso = applyTemplate(afmt, dictTemp_afmt).replace(/<br\s*\/?>/gi, "\n").replace(/<hr\s*\/?>/gi, "\n───────────────\n");
    this._updateFlashcardContent();
  },

  /**
   * Load stylesheet.
   * @param {String} stylesheetPath Path to stylesheet.css.
   */
  _loadStylesheet: function(stylesheetPath) {
    const themeContext = St.ThemeContext.get_for_stage(global.stage);
    const theme = themeContext.get_theme();

    if (GLib.file_test(stylesheetPath, GLib.FileTest.EXISTS)) {
      theme.load_stylesheet(stylesheetPath); // utilise directement le chemin
      global.log("✅ Feuille de style chargée : " + stylesheetPath);
    } else {
      global.log("❌ Feuille de style introuvable : " + stylesheetPath);
    }
  },

  /**
   * Read a JSON file that contains the result of a query. The result is the data to display.
   */
  _readJson: function() {
    try {
      const file = Gio.File.new_for_path(this.queryRes);
      const [success, contents, etag] = file.load_contents(null);

      let decoder = new TextDecoder("utf-8");
      let jsonString = decoder.decode(contents);
      const data = JSON.parse(jsonString); // tags, flds, sfld, qfmt, afmt

      if (Array.isArray(data)) {
        this._getData(data, 0);
        this._data = data;
      } else if (data.error) {
        this.flashcardLabel.set_text(data.error);
      } else {
        this.flashcardLabel.set_text("Format JSON inattendu.");
      }

    } catch (e) {
      this.flashcardLabel.set_text(e.message)
    }
  }
};

