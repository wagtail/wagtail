/* eslint-disable dot-notation */

import Telepath from './Telepath';

const telepath = new Telepath();

class Artist {
  constructor(name) {
    this.name = name;
  }
}

telepath.register('music.Artist', Artist);

class Album {
  constructor(title, artists) {
    this.title = title;
    this.artists = artists;
  }
}

telepath.register('music.Album', Album);

describe('Telepath', () => {
  it('can unpack objects', () => {
    const beyonce = telepath.unpack({ _type: 'music.Artist', _args: ['Beyoncé'] });
    expect(beyonce.name).toBe('Beyoncé');
  });

  it('can unpack lists', () => {
    const destinysChild = telepath.unpack([
      { _type: 'music.Artist', _args: ['Beyoncé'] },
      { _type: 'music.Artist', _args: ['Kelly Rowland'] },
      { _type: 'music.Artist', _args: ['Michelle Williams'] },
    ]);
    expect(destinysChild.length).toBe(3);
    expect(destinysChild[0].name).toBe('Beyoncé');
  });

  it('can unpack dicts', () => {
    const glastonbury = telepath.unpack({
      pyramid_stage: { _type: 'music.Artist', _args: ['Beyoncé'] },
      acoustic_stage: { _type: 'music.Artist', _args: ['Ed Sheeran'] },
    });
    expect(glastonbury.pyramid_stage.name).toBe('Beyoncé');
  });

  it('can unpack dicts in verbose form', () => {
    const profile = telepath.unpack({
      _dict: {
        _artist: { _type: 'music.Artist', _args: ['Beyoncé'] },
        _type: 'R&B',
      }
    });
    expect(profile['_artist'].name).toBe('Beyoncé');
    expect(profile['_type']).toBe('R&B');
  });

  it('can recursively unpack objects in parameters', () => {
    const dangerouslyInLove = telepath.unpack({
      _type: 'music.Album',
      _args: [
        'Dangerously in Love',
        [
          { _type: 'music.Artist', _args: ['Beyoncé'] },
        ]
      ]
    });
    expect(dangerouslyInLove.title).toBe('Dangerously in Love');
    expect(dangerouslyInLove.artists[0].name).toBe('Beyoncé');
  });
});
