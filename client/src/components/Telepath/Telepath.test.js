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

  it('can expand object references', () => {
    const discography = telepath.unpack([
      {
        _type: 'music.Album',
        _args: [
          'Dangerously in Love',
          [
            { _type: 'music.Artist', _args: ['Beyoncé'], _id: 0 },
          ]
        ]
      },
      {
        _type: 'music.Album',
        _args: [
          'Everything Is Love',
          [
            { _ref: 0 },
            { _type: 'music.Artist', _args: ['Jay-Z'] },
          ]
        ]
      },
    ]);
    expect(discography[0].artists[0].name).toBe('Beyoncé');
    expect(discography[1].artists[0].name).toBe('Beyoncé');
    expect(discography[1].artists[1].name).toBe('Jay-Z');
  });

  it('can expand list references', () => {
    const discography = telepath.unpack([
      {
        _type: 'music.Album',
        _args: [
          "Destiny's Child",
          {
            _list: [
              { _type: 'music.Artist', _args: ['Beyoncé'] },
              { _type: 'music.Artist', _args: ['Kelly Rowland'] },
              { _type: 'music.Artist', _args: ['Michelle Williams'] },
            ],
            _id: 0,
          }
        ]
      },
      {
        _type: 'music.Album',
        _args: [
          'Survivor',
          { _ref: 0 },
        ]
      },
    ]);
    expect(discography[1].artists.length).toBe(3);
    expect(discography[1].artists[0].name).toBe('Beyoncé');
    expect(discography[1].artists).toBe(discography[0].artists);
  });

  it('can expand primitive value references', () => {
    const discography = telepath.unpack([
      {
        _type: 'music.Album',
        _args: [
          'Dangerously in Love',
          [
            {
              _type: 'music.Artist',
              _args: [{ _val: 'Beyoncé', _id: 0 }],
              _id: 1,
            },
          ]
        ]
      },
      {
        _type: 'music.Album',
        _args: [
          { _ref: 0 },
          [
            { _ref: 1 },
          ]
        ]
      },
    ]);
    expect(discography[0].artists[0].name).toBe('Beyoncé');
    expect(discography[1].title).toBe('Beyoncé');
    expect(discography[1].artists[0].name).toBe('Beyoncé');
  });
});
