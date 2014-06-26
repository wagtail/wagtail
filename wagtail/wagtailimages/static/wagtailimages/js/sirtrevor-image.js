SirTrevor.Blocks.Image = SirTrevor.Block.extend({
  
    type: "image",
    title: "Image",
  
    icon_name: 'image',

    onBlockRender: function(){
      if (this.imageData === undefined) {
        var st_ref = this;
        return ModalWorkflow({
          url: window.chooserUrls.imageChooser + '?select_format=true',
          st: st_ref,
          responses: {
            imageChosen: function(imageData) {
              this.st.imageData = imageData;
              this.st.setData(imageData);
              this.st.$editor.html(imageData.html)
              this.st.ready();
            }
          }
        });
      }
    },

    toData: function() {
      this.setData(this.imageData);
    },

    loadData: function(data){
      this.imageData = data;
      this.$editor.html(data.html)
    }

  });