(function ($) {
    var fontFamily = 'PingFang SC, Lantinghei SC, Microsoft Yahei, Hiragino Sans GB, Microsoft Sans Serif, WenQuanYi Micro Hei, sans'

    var NODAL_HTML = [
        '<div class="attr-modal modal fade" tabindex="-1" role="dialog" aria-labelledby="entityInfoModalTitle" aria-hidden="true">',
            '<div class="modal-dialog modal-lg">',
                '<div class="modal-content">',
                    '<div class="modal-header">',
                        '<h4 class="modal-title">详细信息</h4>',
                        '<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>',
                    '</div>',
                    '<div class="modal-body" style="max-height:800px;overflow:auto;">',
                        '<img class="entity-info-img center-block pb-3" style="max-width: 200px;"/>',
                        '<table class="table">',
                            '<tbody class="info-table"></tbody>',
                        '</table>',
                    '</div>',
                '</div>',
            '</div>',
        '</div>',
    ].join('\n');

    /**
     * 
     * options.data:  后端传来的数据
     */
    $.fn.graph = function (options) {
        if (!this.data('graph')) {
            this.data('graph', new Graph(this, options));
        } else {
            this.data('graph').update(options);
        }
    };


    function Graph($el, options) {
        this.$el = $el;
        this.options = options;
        this.$modal = this.createModal();
        this.chart = echarts.init(this.$el.get(0));
        if (options.click !== false) {
            this.bindClickEvent();
        }
        this.draw();
    };

    Graph.prototype.draw = function () {
        var option = this.getEchartsOption();
        this.chart.clear();
        this.chart.setOption(option);
    };

    Graph.prototype.createModal = function () {
        var $div = $('<div></div>').html(NODAL_HTML);
        var $modal = $div.find('.modal');
        $('body').append($modal);
        return $modal;
    };

    Graph.prototype.update = function (options) {
        this.options = options;
        this.draw();
    };

    Graph.prototype.bindClickEvent = function () {
        var _this = this;
        this.chart.on('click', function (event) {
            if (event.dataType === 'node') {
                var neoId = event.data.neoId;
                var name = event.name;
                var $title = _this.$modal.find('.modal-title');
                var $table = _this.$modal.find('.info-table');
                var $image = _this.$modal.find('.entity-info-img');
                var url = "/api/graph/entity?id=" + neoId;
                $.getJSON(url, function (result) {
                    var temp_baidu = "<span class='badge entity-source' style='background-color:green'>百度</span>";
                    var temp_hudong = "<span class='badge entity-source' style='background-color:orange'>互动</span>";
                    var temp_zhwiki = "<span class='badge entity-source' style='background-color:blue'>维基</span>";

                    $title.text(name);

                    $table.empty();
                    for (var key in result) {
                        if (result.hasOwnProperty(key)) {
                            var value = result[key];
                            if ((value.indexOf("[HD]") !== 0) && (value.indexOf("[ZHWIKI]") !== 0)) {
                                value = temp_baidu + value;
                            }
                            value = value.replace("[HD]", temp_hudong);
                            value = value.replace("[ZHWIKI]", temp_zhwiki);
                            $table.append("<tr><td style='width: 100px;font-weight: 600;'>" + key + "</td><td>" + value + "</td></tr>");
                        }
                    }
                });
                _this.$modal.modal();
            }
        })
    };

    Graph.prototype.getEchartsOption = function () {
        var result = this.options.data;

        var nodeSize = 80;
        var dnodeSize = 19;
        var fontSize = 14;
        var nodes = [];
        var links = [];
        var categories = [];
        var answerpath = result.answerpath || [];
        result.nodes.forEach(function (node) {
            if (!node.category) {
                node.category = node.label;
            }

            if (categories.indexOf(node.category) == -1) {
                categories.push(node.category);
            }

            node.value = node.value || 0;
            node.symbol = 'circle';
            node.symbolSize = nodeSize - node.value * dnodeSize;
            node.x = null;
            node.y = null;
            node.itemStyle = null;
            node.label = {
                normal: {
                    show: true,
                    position: 'right'
                }
            };
            nodes.push(node);
        });
        result.links.forEach(function (edge) {
            links.push(edge);
        });
        //点亮寻找的答案轨迹
        nodes.forEach(function (node) {
            if (answerpath.indexOf(node.id) >= 0)
                node.itemStyle = {
                    normal: {
                        borderColor: 'yellow',
                        borderWidth: 10
                    }
                };
        });
        links.forEach(function (link) {
            if ((answerpath.indexOf(link.source) >= 0) && (answerpath.indexOf(link.target) >= 0))
                link.lineStyle = {
                    normal: {
                        color: 'yellow',
                        width: 10
                    }
                };
        });
        categories = categories.map(category => ({
            name: category
        }));

        //开始绘制图像
        var colorPalette = ["#f44336", "#673ab7", "#607d8b", "#009688", "#e91e63", "#ff5722", "#4caf50", "#ff9800", "#8bc34a", "#00bcd4", "#9c27b0"]
        var option = {
            color: colorPalette,
            backgroundColor: 'white',
            title: {
                text: result.answer,
                top: '1%',
                left: '1%',
                textStyle: {
                    color: "#333333",
                    fontSize: fontSize * 1.8,
                    fontWeight: 'bolder'
                },
                subtext: '图中共有 ' + result.nodes.length + ' 个节点以及 ' + result.links.length + ' 条关系',
                subtextStyle: {
                    color: "#333333",
                    fontSize: fontSize,
                    fontWeight: 'bold'
                }
            },
            tooltip: {
                formatter: function (params) {
                    if (params.dataType === 'node')
                        return params.data.category;
                    else
                        return params.data.name;
                }
            },
            legend: {
                data: categories,
                bottom: '1%',
                left: '1%',
                orient: 'vertical',
                selectedMode: false,
                textStyle: {
                    color: '#333',
                    fontSize: fontSize * 0.9,
                    fontWeight: 'bold'
                }
            },
            series: [{
                type: 'graph',
                layout: 'force',
                data: nodes,
                links: links,
                // edgeSymbol: ['', 'arrow'],
                categories: categories,
                lineStyle: {
                    color: 'source',
                    curveness: 0.3
                },
                emphasis: {
                    lineStyle: {
                        width: 5
                    }
                },
                force: {
                    repulsion: 1000,
                    layoutAnimation: false
                },
                roam: true,
                focusNodeAdjacency: true,
                animationDuration: 2000
            }],
            textStyle: {
                fontFamily: fontFamily,
                fontSize: fontSize,
                fontWeight: 'bold'
            }
        };

        this.override(option)

        return option;
    };

    Graph.prototype.override = function(chartOption){
        if(this.options.override){
            this.options.override(chartOption)
        }
    };



})(jQuery);